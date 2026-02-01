from fastapi import FastAPI, Depends, HTTPException, Query, Request
from .database_firestore import FirestoreDB
from .calendar_service import CalendarService
from datetime import datetime, date
from dateutil import parser
from fastapi.middleware.cors import CORSMiddleware
from .ai_agent import RotaAI
import os

app = FastAPI(title="Teacher Cover Rota API (Firestore)")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ai_assistant = RotaAI()

# --- BULK IMPORT (The Bridge) ---
@app.post("/api/import-staff")
async def import_staff_bridge(request: Request):
    """
    Receives JSON list and saves to Firestore. 
    Using Request object to bypass FastAPI's multipart check.
    """
    try:
        data = await request.json()
    except:
        return {"error": "Invalid JSON"}

    from .database_firestore import get_db
    db = get_db()
    if not db:
        return {"error": "Firestore not connected"}
    
    count = 0
    for s in data:
        try:
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
        except: pass
    return {"imported": count}

# --- Standard Endpoints ---
@app.get("/api/staff")
def get_staff():
    return FirestoreDB.get_staff()

@app.post("/api/absences")
def log_absence(staff_name: str, date: str, start_period: int, end_period: int):
    staff = FirestoreDB.get_staff_member(name=staff_name)
    if not staff:
        raise HTTPException(status_code=404, detail=f"Staff '{staff_name}' not found")
    target_date = parser.parse(date).strftime('%Y-%m-%d')
    absence_id = FirestoreDB.add_absence(staff["id"], staff["name"], target_date, start_period, end_period)
    return {"id": absence_id, "status": "created"}

@app.get("/api/suggest-cover/{absence_id}")
def suggest_cover(absence_id: int, day: str = "Monday"):
    abs_id_str = str(absence_id)
    try:
        absences = FirestoreDB.get_absences()
        absence = next((a for a in absences if a["id"] == abs_id_str), None)
        if not absence:
            raise HTTPException(status_code=404, detail="Absence not found")
        
        absent_staff_id = absence["staff_id"]
        all_staff = FirestoreDB.get_staff()
        absent_schedules = FirestoreDB.get_schedules(absent_staff_id, day=day)
        absent_sched_map = {sch["period"]: sch for sch in absent_schedules if not sch["is_free"]}
        all_range_periods = list(range(absence["start_period"], absence["end_period"] + 1))
        target_periods = [p for p in all_range_periods if p in absent_sched_map]
        
        available_profiles = []
        for s in all_staff:
            if s["id"] == absent_staff_id: continue
            s_schedules = FirestoreDB.get_schedules(s["id"], day=day)
            free_periods = [sch["period"] for sch in s_schedules if sch["is_free"]]
            busy_periods = {sch["period"]: sch["activity"] for sch in s_schedules if not sch["is_free"]}
            available_profiles.append({
                "name": s["name"], "role": s.get("role", "Teacher"), "profile": s.get("profile"),
                "is_priority": s.get("is_priority", False), "is_specialist": s.get("is_specialist", False),
                "free_periods": free_periods, "busy_periods": busy_periods
            })

        ai_response = ai_assistant.suggest_cover(
            absent_staff=absence["staff_name"], day=day,
            periods=target_periods, available_staff_profiles=available_profiles
        )
        return {"suggestions": ai_response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/availability")
def check_availability(periods: str, day: str = "Monday", date: str = None):
    try:
        period_list = [int(p) for p in periods.split(',') if p]
        all_staff = FirestoreDB.get_staff()
        staff = [s for s in all_staff if s.get("is_active", True) and s.get("can_cover_periods", True)]
        # ... simplified logic to just return staff for now to verify connection
        return [{"name": s["name"], "is_free": True} for s in staff]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/assign-cover")
def assign_cover_api(absence_id: str, staff_name: str, periods: str):
    staff = FirestoreDB.get_staff_member(name=staff_name)
    if not staff: raise HTTPException(status_code=404)
    period_list = [int(p) for p in periods.split(',') if p]
    for p in period_list:
        FirestoreDB.assign_cover(str(absence_id), staff["id"], staff["name"], p)
    return {"status": "ok"}

@app.get("/api/daily-rota")
def get_daily_rota(date: str):
    target_date = parser.parse(date).strftime('%Y-%m-%d')
    absences = FirestoreDB.get_absences(date=target_date)
    return absences

@app.delete("/api/unassign-cover")
def unassign_cover_api(absence_id: str, period: int):
    FirestoreDB.unassign_cover(str(absence_id), period)
    return {"status": "ok"}
