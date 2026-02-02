from fastapi import FastAPI, Request
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
async def root():
    return {"status": "online", "message": "RotaAI is running on Render!"}

# 2. HEALTH CHECK (Fast)
@app.get("/api/health")
async def health():
    info = {"status": "online", "version": "3.0.3", "platform": "Render"}
    try:
        from backend.database_firestore import get_db, FirestoreDB
        db = get_db()
        info["db"] = "connected" if db else "failed"
        if db:
            info["staff_count"] = len(FirestoreDB.get_staff())
    except Exception as e:
        info["db"] = f"error: {str(e)}"
    return info

# 3. IMPORT DATA BRIDGE
@app.post("/api/import-staff")
async def handle_import(request: Request):
    try:
        data = await request.json()
        from backend.database_firestore import get_db
        db = get_db()
        if not db:
            return JSONResponse(status_code=500, content={"error": "Database not connected"})
        
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
        return {"imported": count}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "trace": traceback.format_exc()}
        )

# 4. LOAD FULL API ENDPOINTS
# We import these at the bottom to ensure they can access 'app' if needed,
# or we can manually register them. For Render, we'll keep them in this file for safety.

from backend.database_firestore import FirestoreDB
from dateutil import parser
from fastapi import HTTPException

@app.get("/api/staff")
async def get_all_staff():
    return FirestoreDB.get_staff()

@app.get("/api/daily-rota")
async def get_daily_rota(date: str):
    target_date = parser.parse(date).strftime('%Y-%m-%d')
    return FirestoreDB.get_absences(date=target_date)

@app.post("/api/absences")
async def log_absence(staff_name: str, date: str, start_period: int, end_period: int):
    staff = FirestoreDB.get_staff_member(name=staff_name)
    if not staff:
        raise HTTPException(status_code=404, detail=f"Staff '{staff_name}' not found")
    target_date = parser.parse(date).strftime('%Y-%m-%d')
    absence_id = FirestoreDB.add_absence(staff["id"], staff["name"], target_date, start_period, end_period)
    return {"id": absence_id, "status": "created"}

@app.get("/api/suggest-cover/{absence_id}")
async def suggest_cover(absence_id: str, day: str = "Monday"):
    try:
        absences = FirestoreDB.get_absences()
        absence = next((a for a in absences if a["id"] == absence_id), None)
        if not absence:
            raise HTTPException(status_code=404, detail="Absence not found")
        
        absent_staff_id = absence["staff_id"]
        all_staff = FirestoreDB.get_staff()
        
        # Suggestion logic relies on AI
        from backend.ai_agent import RotaAI
        ai = RotaAI()
        
        # Build profiles for AI
        available_profiles = []
        for s in all_staff:
            if s["id"] == absent_staff_id: continue
            s_schedules = FirestoreDB.get_schedules(s["id"], day=day)
            available_profiles.append({
                "name": s["name"], "role": s.get("role", "Teacher"),
                "is_priority": s.get("is_priority", False),
                "free_periods": [sch["period"] for sch in s_schedules if sch["is_free"]]
            })

        ai_response = ai.suggest_cover(
            absent_staff=absence["staff_name"], day=day,
            periods=[absence["start_period"]], # Simplified for now
            available_staff_profiles=available_profiles
        )
        return {"suggestions": ai_response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
