import openpyxl
import os
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from . import database
from .database import engine, SessionLocal, Staff, Schedule, Absence, Cover, Setting
from .calendar_service import CalendarService
import pandas as pd
from fastapi.middleware.cors import CORSMiddleware
from .ai_agent import RotaAI
import json

app = FastAPI(title="Teacher Cover Rota API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    database.Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"Database sync error: {e}")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

ai_assistant = RotaAI()

@app.get("/")
def read_root():
    return {"message": "Teacher Cover Rota API is running"}

@app.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    return {
        "staff_count": db.query(Staff).count(),
        "absence_count": db.query(Absence).count(),
        "cover_count": db.query(Cover).count()
    }

@app.get("/normalize-legacy")
def trigger_normalize_legacy():
    try:
        from .normalize_legacy import normalize_legacy_absences
        normalize_legacy_absences()
        return {"status": "success", "message": "Legacy absences normalized."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/fix-duplicates")
def trigger_fix_duplicates(db: Session = Depends(get_db)):
    try:
        from .fix_duplicates import run_merge_in_session
        logs = run_merge_in_session(db)
        return {"status": "success", "logs": logs}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/staff")
def get_staff(db: Session = Depends(get_db)):
    return db.query(Staff).all()

@app.post("/absences")
def log_absence(staff_name: str, date: str, start_period: int, end_period: int, db: Session = Depends(get_db)):
    staff = db.query(Staff).filter(func.lower(Staff.name) == staff_name.lower()).first()
    if not staff:
        raise HTTPException(status_code=404, detail=f"Staff '{staff_name}' not found")
    
    target_date = pd.to_datetime(date).date()
    
    existing_absence = db.query(Absence).filter(
        Absence.staff_id == staff.id,
        Absence.date == target_date
    ).first()
    
    if existing_absence:
        existing_absence.start_period = start_period
        existing_absence.end_period = end_period
        db.commit()
        db.refresh(existing_absence)
        return existing_absence
    
    new_absence = Absence(
        staff_id=staff.id,
        date=target_date,
        start_period=start_period,
        end_period=end_period
    )
    db.add(new_absence)
    db.commit()
    db.refresh(new_absence)
    return new_absence

@app.get("/suggest-cover/{absence_id}")
def suggest_cover(absence_id: int, day: str = "Monday", db: Session = Depends(get_db)):
    try:
        absence = db.query(Absence).filter(Absence.id == absence_id).first()
        if not absence:
            raise HTTPException(status_code=404, detail="Absence not found")
        
        absent_staff = db.query(Staff).filter(Staff.id == absence.staff_id).first()
        absent_schedules = {sch.period: sch for sch in absent_staff.schedules if sch.day_of_week.lower() == day.lower()}
        
        all_range_periods = list(range(absence.start_period, absence.end_period + 1))
        target_periods = [p for p in all_range_periods if p in absent_schedules and not absent_schedules[p].is_free]
        
        potential_staff = db.query(Staff).filter(Staff.is_active == True).all()
        available_profiles = []
        
        for s in potential_staff:
            if s.id == absent_staff.id:
                continue
                
            free_periods = [sch.period for sch in s.schedules if sch.is_free and sch.day_of_week.lower() == day.lower()]
            busy_periods = {sch.period: sch.activity for sch in s.schedules if not sch.is_free and sch.day_of_week.lower() == day.lower()}

            calendar_events = {}
            if s.calendar_url:
                try:
                    target_dt = pd.to_datetime(absence.date).date()
                    calendar_events = CalendarService.get_busy_periods(s.calendar_url, target_dt)
                    free_periods = [p for p in free_periods if p not in calendar_events]
                except Exception:
                    pass

            available_profiles.append({
                "name": s.name,
                "role": s.role,
                "can_cover_periods": s.can_cover_periods,
                "profile": s.profile,
                "is_priority": s.is_priority,
                "is_specialist": s.is_specialist,
                "free_periods": free_periods,
                "busy_periods": busy_periods,
                "calendar_events": calendar_events
            })

        ai_response = ai_assistant.suggest_cover(
            absent_staff=absent_staff.name,
            day=day,
            periods=target_periods,
            available_staff_profiles=available_profiles
        )
        
        return {
            "absence_id": absence_id,
            "absent_teacher": absent_staff.name,
            "day": day,
            "periods": target_periods,
            "suggestions": ai_response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/availability")
def check_availability(periods: str, day: str = "Monday", date: str = None, db: Session = Depends(get_db)):
    try:
        period_list = [int(p) for p in periods.split(',') if p]
        has_teaching_periods = any(1 <= p <= 8 for p in period_list)
        
        query = db.query(Staff).filter(Staff.is_active == True)
        if has_teaching_periods:
            query = query.filter(Staff.can_cover_periods == True)
            
        staff = query.all()
        
        if date:
            target_dt = pd.to_datetime(date).date()
        else:
            target_dt = pd.Timestamp.now().date()
            
        active_covers = db.query(Cover).join(Absence).filter(Absence.date == target_dt).all()
        cover_map = {}
        for c in active_covers:
            if c.covering_staff_id not in cover_map:
                cover_map[c.covering_staff_id] = {}
            cover_map[c.covering_staff_id][c.period] = c.absence.staff.name

        results = []
        for s in staff:
            day_schedules = {sch.period: sch for sch in s.schedules if sch.day_of_week.lower() == day.lower()}
            staff_covers = cover_map.get(s.id, {})
            
            calendar_busy = []
            if s.calendar_url:
                try:
                    calendar_busy = CalendarService.get_busy_periods(s.calendar_url, target_dt)
                except:
                    pass
            
            is_all_free = True
            first_busy_reason = None

            for p in period_list:
                is_timetable_free = day_schedules.get(p) and day_schedules[p].is_free
                who_covering = staff_covers.get(p)
                is_calendar_busy = p in calendar_busy
                
                if who_covering:
                    is_all_free = False
                    first_busy_reason = f"Covering {who_covering}"
                    break
                elif is_calendar_busy:
                    is_all_free = False
                    first_busy_reason = calendar_busy[p]
                    break
                elif not is_timetable_free:
                    is_all_free = False
                    first_busy_reason = day_schedules[p].activity if day_schedules.get(p) else "Busy"
                    break
            
            if is_all_free:
                display_activity = "Free"
                if not s.is_specialist:
                    reasons = []
                    for p in period_list:
                        act = day_schedules[p].activity if day_schedules.get(p) else ""
                        if act and act.lower() not in ['free', 'none', 'available', '']:
                            reasons.append(act)
                    if reasons:
                        display_activity = f"class doing {', '.join(reasons)}" if len(reasons) == 1 else "Various Activities"

                results.append({
                    "name": s.name, 
                    "profile": s.profile, 
                    "is_priority": s.is_priority,
                    "is_specialist": s.is_specialist,
                    "is_free": True,
                    "activity": display_activity
                })
            elif s.is_specialist:
                results.append({
                    "name": s.name, 
                    "profile": s.profile, 
                    "is_priority": s.is_priority,
                    "is_specialist": True,
                    "is_free": False,
                    "activity": first_busy_reason
                })
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/assign-cover")
def assign_cover(absence_id: int, staff_name: str, periods: str, db: Session = Depends(get_db)):
    try:
        staff = db.query(Staff).filter(func.lower(Staff.name) == staff_name.lower()).first()
        if not staff:
            raise HTTPException(status_code=404, detail="Cover staff not found")
        period_list = [int(p) for p in periods.split(',') if p]
        for p in period_list:
            existing = db.query(Cover).filter(Cover.absence_id == absence_id, Cover.period == p).first()
            if existing:
                existing.covering_staff_id = staff.id
            else:
                db.add(Cover(absence_id=absence_id, covering_staff_id=staff.id, period=p, status="confirmed"))
        db.commit()
        return {"message": f"Assigned {staff_name} to periods {periods}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/covers/{absence_id}")
def get_covers(absence_id: int, db: Session = Depends(get_db)):
    covers = db.query(Cover).filter(Cover.absence_id == absence_id).all()
    return [{"period": c.period, "staff_name": c.covering_staff.name} for c in covers]

@app.get("/staff-schedule/{staff_name}")
def get_staff_schedule(staff_name: str, day: str = None, db: Session = Depends(get_db)):
    staff = db.query(Staff).filter(func.lower(Staff.name) == staff_name.lower()).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff member not found")
    
    query = db.query(Schedule).filter(Schedule.staff_id == staff.id)
    if day:
        query = query.filter(func.lower(Schedule.day_of_week) == day.lower())
    
    schedules = query.order_by(Schedule.period).all()
    return [{
        "period": s.period,
        "day": s.day_of_week,
        "activity": s.activity,
        "is_free": s.is_free
    } for s in schedules]

@app.get("/daily-rota")
def get_daily_rota(date: str, db: Session = Depends(get_db)):
    try:
        target_date = pd.to_datetime(date).date()
        absences = db.query(Absence).filter(Absence.date == target_date).all()
        
        results = []
        for a in absences:
            covers = []
            for c in a.covers:
                covers.append({
                    "period": c.period,
                    "covering_staff_name": c.covering_staff.name if c.covering_staff else "Unknown"
                })
            
            results.append({
                "absence_id": a.id,
                "staff_name": a.staff.name,
                "start_period": a.start_period,
                "end_period": a.end_period,
                "covers": covers
            })
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/unassign-cover")
def unassign_cover(absence_id: int, period: int, db: Session = Depends(get_db)):
    try:
        db.query(Cover).filter(Cover.absence_id == absence_id, Cover.period == period).delete()
        db.commit()
        return {"message": f"Unassigned period {period}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/generate-report")
def generate_report(query: str, db: Session = Depends(get_db)):
    try:
        absences = db.query(Absence).all()
        covers = db.query(Cover).all()
        
        data_summary = "Staff Absences:\n"
        for a in absences[-1000:]:
            data_summary += f"- Staff: {a.staff.name}, Date: {a.date}, Periods: {a.start_period}-{a.end_period}\n"
        
        data_summary += "\nCover Assignments:\n"
        for c in covers[-1000:]:
             data_summary += f"- Covering Staff: {c.covering_staff.name}, Covered For: {c.absence.staff.name}, Date: {c.absence.date}, Period: {c.period}\n"
        
        report = ai_assistant.generate_report(query, data_summary)
        return {"report": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
