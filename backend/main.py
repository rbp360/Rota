from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from . import database
from .database import engine, SessionLocal, Staff, Schedule, Absence, Cover, Setting
import pandas as pd
import os

from fastapi.middleware.cors import CORSMiddleware

database.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Teacher Cover Rota API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Temporarily broad to debug network issues
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "Teacher Cover Rota API is running"}

@app.get("/staff")
def get_staff(db: Session = Depends(get_db)):
    return db.query(Staff).all()

from sqlalchemy import func

@app.post("/absences")
def log_absence(staff_name: str, date: str, start_period: int, end_period: int, db: Session = Depends(get_db)):
    staff = db.query(Staff).filter(func.lower(Staff.name) == staff_name.lower()).first()
    if not staff:
        raise HTTPException(status_code=404, detail=f"Staff '{staff_name}' not found")
    
    new_absence = Absence(
        staff_id=staff.id,
        date=pd.to_datetime(date).date(),
        start_period=start_period,
        end_period=end_period
    )
    db.add(new_absence)
    db.commit()
    db.refresh(new_absence)
    return new_absence

from .ai_agent import RotaAI
import json

ai_assistant = RotaAI()

@app.get("/suggest-cover/{absence_id}")
def suggest_cover(absence_id: int, day: str = "Monday", db: Session = Depends(get_db)):
    try:
        absence = db.query(Absence).filter(Absence.id == absence_id).first()
        if not absence:
            raise HTTPException(status_code=404, detail="Absence not found")
        
        absent_staff = db.query(Staff).filter(Staff.id == absence.staff_id).first()
        target_periods = list(range(absence.start_period, absence.end_period + 1))
        
        # Get all potential covering staff
        potential_staff = db.query(Staff).filter(Staff.is_active == True).all()
        available_profiles = []
        
        for s in potential_staff:
            if s.id == absent_staff.id:
                continue
                
            # Filter schedules by the selected day
            free_periods = [sch.period for sch in s.schedules if sch.is_free and sch.day_of_week.lower() == day.lower()]
            
            available_profiles.append({
                "name": s.name,
                "profile": s.profile,
                "is_priority": s.is_priority,
                "is_specialist": s.is_specialist,
                "free_periods": free_periods
            })

        # Call AI
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
        print(f"Backend Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/availability")
def check_availability(periods: str, day: str = "Monday", db: Session = Depends(get_db)):
    try:
        period_list = [int(p) for p in periods.split(',') if p]
        staff = db.query(Staff).filter(Staff.is_active == True).all()
        
        # Fetch ALL covers for today to check if teachers are already busy covering others
        # We assume "today" is the date of the absence we are managing
        today = pd.Timestamp.now().date()
        active_covers = db.query(Cover).join(Absence).filter(Absence.date == today).all()
        
        # Organize covers by staff_id and period for quick lookup
        # cover_map[staff_id][period] = "Name of person they are covering"
        cover_map = {}
        for c in active_covers:
            if c.covering_staff_id not in cover_map:
                cover_map[c.covering_staff_id] = {}
            cover_map[c.covering_staff_id][c.period] = c.absence.staff.name

        results = []
        for s in staff:
            # 1. Check their base timetable
            day_schedules = {sch.period: sch for sch in s.schedules if sch.day_of_week.lower() == day.lower()}
            
            # 2. check their "Live" covers
            staff_covers = cover_map.get(s.id, {})
            
            # Check if they are free in ALL requested periods
            # They are free ONLY if: 
            # (a) their schedule says they are free AND (b) they aren't already covering someone
            is_all_free = True
            first_busy_reason = None

            for p in period_list:
                # check timetable
                is_timetable_free = day_schedules.get(p) and day_schedules[p].is_free
                
                # check existing covers
                who_covering = staff_covers.get(p)
                
                if who_covering:
                    is_all_free = False
                    first_busy_reason = f"Covering {who_covering}"
                    break
                elif not is_timetable_free:
                    is_all_free = False
                    first_busy_reason = day_schedules[p].activity if day_schedules.get(p) else "Busy"
                    break
            
            if is_all_free:
                # Determine display activity
                display_activity = "Free"
                # If they are a form teacher and have an activity, it's likely a specialist lesson (e.g. "6 RG Music")
                # We can find the activity from the schedule
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
                # Specialists always shown, but marked red if busy
                results.append({
                    "name": s.name, 
                    "profile": s.profile, 
                    "is_priority": s.is_priority,
                    "is_specialist": True,
                    "is_free": False,
                    "activity": first_busy_reason
                })
            # Form teachers (not specialists) are hidden if busy
            
        return results
    except Exception as e:
        print(f"Availability Error: {e}")
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

@app.delete("/unassign-cover")
def unassign_cover(absence_id: int, period: int, db: Session = Depends(get_db)):
    try:
        db.query(Cover).filter(Cover.absence_id == absence_id, Cover.period == period).delete()
        db.commit()
        return {"message": f"Unassigned period {period}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
