from fastapi import FastAPI, Depends, HTTPException, Query, Request
from .database_firestore import FirestoreDB
from .calendar_service import CalendarService
from datetime import datetime, date
from dateutil import parser
from fastapi.middleware.cors import CORSMiddleware
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

# Lazy AI Helper
_ai = None
def get_ai():
    global _ai
    if _ai is None:
        try:
            from .ai_agent import RotaAI
            _ai = RotaAI()
        except Exception as e:
            print(f"AI initialization failed: {e}")
            return None
    return _ai

# API Endpoints
@app.get("/api/health")
def health_check():
    db_status = "unknown"
    staff_count = 0
    try:
        from .database_firestore import get_db, FirestoreDB
        db = get_db()
        db_status = "connected" if db else "failed"
        if db:
            staff_count = len(FirestoreDB.get_staff())
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "ok",
        "version": "1.9.0",
        "db": db_status,
        "staff_count": staff_count,
        "environment": "vercel"
    }

@app.post("/api/import-staff")
async def import_staff_bridge(request: Request):
    try:
        data = await request.json()
    except:
        return {"error": "Invalid JSON"}

    from .database_firestore import get_db
    db = get_db()
    if not db:
        return {"error": "Firestore not connected"}
    
    count = 0
    # Use a Write Batch for each request to be much faster
    batch = db.batch()
    
    for s in data:
        try:
            staff_id = str(s["id"])
            staff_ref = db.collection("staff").document(staff_id)
            
            # 1. Update/Set staff info in batch
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

            # 2. Add schedules to batch if present
            if "schedules" in s:
                for sch in s["schedules"]:
                    sched_id = f"{sch['day_of_week']}_{sch['period']}"
                    sched_ref = staff_ref.collection("schedules").document(sched_id)
                    batch.set(sched_ref, sch)
            
            count += 1
        except Exception as e:
            print(f"Error preparing batch for {s.get('name')}: {e}")

    # Commit all operations at once
    try:
        batch.commit()
        return {"imported": count, "status": "success"}
    except Exception as e:
        print(f"BATCH COMMIT FAILED: {e}")
        return {"error": str(e), "imported": 0}

@app.get("/api/staff")
def get_staff():
    return FirestoreDB.get_staff()

@app.post("/api/import-absences")
async def import_absences_bridge(request: Request):
    try:
        data = await request.json()
    except:
        return {"error": "Invalid JSON"}

    from .database_firestore import get_db
    db = get_db()
    if not db:
        return {"error": "Firestore not connected"}
    
    count = 0
    batch = db.batch()
    
    for a in data:
        try:
            abs_id = str(a["id"])
            abs_ref = db.collection("absences").document(abs_id)
            
            # 1. Main Absence record
            batch.set(abs_ref, {
                "staff_id": str(a["staff_id"]),
                "staff_name": a["staff_name"],
                "date": a["date"],
                "start_period": a.get("start_period"),
                "end_period": a.get("end_period")
            })

            # 2. Add covers if present
            if "covers" in a:
                for c in a["covers"]:
                    cover_id = str(c["period"])
                    cover_ref = abs_ref.collection("covers").document(cover_id)
                    batch.set(cover_ref, {
                        "period": c["period"],
                        "staff_name": c["staff_name"],
                        "covering_staff_id": str(c.get("covering_staff_id", ""))
                    })
            
            count += 1
        except Exception as e:
            print(f"Error preparing absence batch: {e}")

    try:
        batch.commit()
        return {"imported_absences": count, "status": "success"}
    except Exception as e:
        print(f"ABSENCE BATCH FAILED: {e}")
        return {"error": str(e), "imported": 0}

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

        ai = get_ai()
        if not ai:
            return {"suggestions": "AI features are currently unavailable on this deployment."}

        ai_response = ai.suggest_cover(
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
        return [{"name": s["name"], "is_free": True} for s in staff]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/daily-rota")
def get_daily_rota(date: str):
    target_date = parser.parse(date).strftime('%Y-%m-%d')
    absences = FirestoreDB.get_absences(date=target_date)
    return absences
