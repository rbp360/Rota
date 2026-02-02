from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
import traceback

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = FastAPI(title="RotaAI Render API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. ROOT STATUS
@app.get("/")
def root():
    return {
        "status": "online", 
        "message": "RotaAI is running on Render!", 
        "version": "4.8.0",
        "hint": "Check /api/health for DB status"
    }

# 2. HEALTH CHECK (Robust Handshake)
@app.get("/api/health")
def health():
    info = {"status": "online", "version": "4.8.0", "platform": "Render"}
    try:
        from backend.database_firestore import get_db
        print("[HEALTH] Checking DB connection...")
        db = get_db()
        if db:
            # Quick real read check
            try:
                db.collection("staff").limit(1).get(timeout=5)
                info["db"] = "connected_and_verified"
                print("[HEALTH] DB verified.")
            except Exception as e:
                info["db"] = "connected_but_no_response"
                info["db_error"] = str(e)
                print(f"[HEALTH] DB verify failed: {e}")
        else:
            info["db"] = "initialization_failed"
            info["error"] = os.environ.get("FIREBASE_INIT_ERROR", "No init error logged")
            print("[HEALTH] DB init failed.")
    except Exception as e:
        info["status"] = "unstable"
        info["error"] = str(e)
        print(f"[HEALTH] Crash: {e}")
    return info

# 3. IMPORT DATA BRIDGE (Batch mode for speed)
@app.post("/api/import-staff")
async def handle_import(request: Request):
    try:
        data = await request.json()
        print(f"[IMPORT] Processing {len(data)} items...")
        
        from backend.database_firestore import get_db
        db = get_db()
        if not db:
            return JSONResponse(status_code=500, content={"error": "Database not connected."})
        
        count = 0
        batch = db.batch()
        
        for i, s in enumerate(data):
            staff_ref = db.collection("staff").document(str(s["id"]))
            # Upsert staff
            batch.set(staff_ref, {
                "name": s["name"],
                "role": s.get("role", "Teacher"),
                "profile": s.get("profile"),
                "is_priority": s.get("is_priority", False),
                "is_specialist": s.get("is_specialist", False),
                "is_active": s.get("is_active", True),
                "can_cover_periods": s.get("can_cover_periods", True),
                "calendar_url": s.get("calendar_url")
            })
            
            # Schedules
            if "schedules" in s:
                for sch in s["schedules"]:
                    sch_ref = staff_ref.collection("schedules").document(f"{sch['day_of_week']}_{sch['period']}")
                    batch.set(sch_ref, sch)
            
            count += 1
            # Commit every 10 to keep batch size manageable
            if i % 10 == 0 and i > 0:
                batch.commit()
                batch = db.batch()
        
        batch.commit()
        print(f"[IMPORT] SUCCESS: {count} teachers processed.")
        return {"imported": count}
        
    except Exception as e:
        print(f"[IMPORT] CRASH: {e}")
        return JSONResponse(status_code=500, content={"error": str(e), "trace": traceback.format_exc()})

# 4. CORE API ROUTES (Lazy Loaded)
@app.get("/api/staff")
def get_all_staff():
    from backend.database_firestore import FirestoreDB
    return FirestoreDB.get_staff()

@app.get("/api/daily-rota")
def get_daily_rota(date: str):
    from backend.database_firestore import FirestoreDB
    from dateutil import parser
    target_date = parser.parse(date).strftime('%Y-%m-%d')
    return FirestoreDB.get_absences(date=target_date)

@app.post("/api/absences")
def log_absence(staff_name: str, date: str, start_period: int, end_period: int):
    from backend.database_firestore import FirestoreDB
    from dateutil import parser
    staff = FirestoreDB.get_staff_member(name=staff_name)
    if not staff:
        raise HTTPException(status_code=404, detail=f"Staff '{staff_name}' not found")
    target_date = parser.parse(date).strftime('%Y-%m-%d')
    absence_id = FirestoreDB.add_absence(staff["id"], staff["name"], target_date, start_period, end_period)
    return {"id": absence_id, "status": "created"}

@app.get("/api/suggest-cover/{absence_id}")
async def suggest_cover(absence_id: str, day: str = "Monday"):
    from backend.database_firestore import FirestoreDB
    try:
        absences = FirestoreDB.get_absences()
        absence = next((a for a in absences if a["id"] == absence_id), None)
        if not absence:
            raise HTTPException(status_code=404, detail="Absence not found")
        
        from backend.ai_agent import RotaAI
        ai = RotaAI()
        all_staff = FirestoreDB.get_staff()
        
        available_profiles = []
        for s in all_staff:
            if s["id"] == absence["staff_id"]: continue
            s_schedules = FirestoreDB.get_schedules(s["id"], day=day)
            available_profiles.append({
                "name": s["name"], "role": s.get("role", "Teacher"),
                "is_priority": s.get("is_priority", False),
                "free_periods": [sch["period"] for sch in s_schedules if sch["is_free"]]
            })

        ai_response = ai.suggest_cover(
            absent_staff=absence["staff_name"], day=day,
            periods=[absence["start_period"]],
            available_staff_profiles=available_profiles
        )
        return {"suggestions": ai_response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
