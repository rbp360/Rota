from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
import traceback

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = FastAPI(title="RotaAI Production API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. ROOT & HEALTH (Mandatory for Render Monitor)
@app.api_route("/", methods=["GET", "HEAD"])
def root():
    return {
        "status": "online", 
        "version": "5.2.0-Audit",
        "message": "RotaAI Backend is Live and Stable"
    }

@app.get("/api/health")
def health():
    return {"status": "ok", "version": "5.2.0-Audit"}

# 2. STAFF ENDPOINTS
@app.get("/api/staff")
def get_staff():
    try:
        from backend.database_firestore import FirestoreDB
        return FirestoreDB.get_staff()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/staff-schedule/{staff_name}")
def get_staff_schedule(staff_name: str, day: str = "Monday"):
    try:
        from backend.database_firestore import FirestoreDB
        staff = FirestoreDB.get_staff_member(name=staff_name)
        if not staff: return []
        return FirestoreDB.get_schedules(staff["id"], day=day)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# 3. ABSENCE & ROTA
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
    
    # We need to implement add_absence if it's missing from FirestoreDB
    db = getattr(FirestoreDB, 'add_absence', None)
    if db:
        aid = FirestoreDB.add_absence(staff["id"], staff["name"], target_date, start_period, end_period)
    else:
        # Fallback inline implementation
        from backend.database_firestore import get_db
        db = get_db()
        absence_ref = db.collection("absences").document()
        absence_ref.set({
            "staff_id": staff["id"],
            "staff_name": staff["name"],
            "date": target_date,
            "start_period": start_period,
            "end_period": end_period,
            "timestamp": firestore.SERVER_TIMESTAMP if 'firestore' in globals() else time.time()
        })
        aid = absence_ref.id
    return {"id": aid, "status": "created"}

# 4. COVER SYSTEM
@app.get("/api/suggest-cover/{absence_id}")
async def suggest_cover(absence_id: str, day: str = "Monday"):
    try:
        from backend.database_firestore import FirestoreDB
        absences = FirestoreDB.get_absences()
        absence = next((a for a in absences if a["id"] == absence_id), None)
        if not absence: raise HTTPException(status_code=404, detail="Absence not found")
        
        # Lazy AI
        from backend.ai_agent import RotaAI
        ai = RotaAI()
        
        all_staff = FirestoreDB.get_staff()
        # Filter and prepare profiles...
        available_profiles = []
        for s in all_staff:
            if s["id"] == absence["staff_id"]: continue
            s_schedules = FirestoreDB.get_schedules(s["id"], day=day)
            available_profiles.append({
                "name": s["name"], "role": s.get("role", "Teacher"),
                "is_priority": s.get("is_priority", False),
                "free_periods": [sch["period"] for sch in s_schedules if sch.get("is_free", False)]
            })

        ai_response = ai.suggest_cover(
            absent_staff=absence["staff_name"], day=day,
            periods=[absence["start_period"]], # Simplified for audit
            available_staff_profiles=available_profiles
        )
        return {"suggestions": ai_response}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/api/import-staff")
async def handle_import(request: Request):
    from backend.main_firestore import import_staff_bridge
    return await import_staff_bridge(request)

# 5. CATCH-ALL FOR DATA INTEGRITY
@app.get("/api/availability")
def check_availability(periods: str, day: str = "Monday", date: str = None):
    # Placeholder for audit
    return []
