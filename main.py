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
        "version": "4.4.0",
        "hint": "Check /api/health for DB status"
    }

# 2. HEALTH CHECK
@app.get("/api/health")
def health():
    info = {"status": "online", "version": "4.4.0", "platform": "Render"}
    try:
        from backend.database_firestore import get_db
        print("Health check: fetching DB...")
        db = get_db()
        if db:
            info["db"] = "connected"
            # Quick network sanity check
            db.collection("staff").limit(1).get()
            info["network"] = "verified"
        else:
            info["db"] = "failed_init"
            info["error"] = os.environ.get("FIREBASE_INIT_ERROR", "Unknown init error")
    except Exception as e:
        info["db"] = "crash"
        info["error"] = str(e)
        print(f"Health Check CRASH: {e}")
    return info

# 3. IMPORT DATA BRIDGE
@app.post("/api/import-staff")
async def handle_import(request: Request):
    try:
        data = await request.json()
        print(f"Importing {len(data)} teachers...")
        from backend.database_firestore import get_db
        db = get_db()
        if not db:
            return JSONResponse(status_code=500, content={"error": "Database not connected."})
        
        count = 0
        for s in data:
            staff_ref = db.collection("staff").document(str(s["id"]))
            staff_ref.set({
                "name": s["name"],
                "role": s.get("role", "Teacher"),
                "profile": s.get("profile"),
                "is_priority": s.get("is_priority", False),
                "is_specialist": s.get("is_specialist", False),
                "is_active": s.get("is_active", True),
                "can_cover_periods": s.get("can_cover_periods", True),
                "calendar_url": s.get("calendar_url")
            })
            if "schedules" in s:
                for sch in s["schedules"]:
                    staff_ref.collection("schedules").document(f"{sch['day_of_week']}_{sch['period']}").set(sch)
            count += 1
        print(f"Import SUCCESS: {count} teachers.")
        return {"imported": count}
    except Exception as e:
        print(f"Import CRASH: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

# 4. CORE API ROUTES
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
