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
        results = []
        for s in staff:
            # Filter schedules for this staff on this day
            day_schedules = {sch.period: sch for sch in s.schedules if sch.day_of_week.lower() == day.lower()}
            
            # Check if they are free in ALL requested periods
            is_all_free = all(day_schedules.get(p) and day_schedules[p].is_free for p in period_list)
            
            if is_all_free:
                results.append({
                    "name": s.name, 
                    "profile": s.profile, 
                    "is_priority": s.is_priority,
                    "is_specialist": s.is_specialist,
                    "is_free": True,
                    "activity": f"Free (Read: '{day_schedules[period_list[0]].activity if period_list else ''}')"
                })
            elif s.is_specialist:
                # Specialist is busy - find out what they are doing in the first busy period
                busy_activity = "Busy"
                for p in period_list:
                    sch = day_schedules.get(p)
                    if sch and not sch.is_free:
                        busy_activity = sch.activity or "Busy"
                        break
                
                results.append({
                    "name": s.name, 
                    "profile": s.profile, 
                    "is_priority": s.is_priority,
                    "is_specialist": True,
                    "is_free": False,
                    "activity": busy_activity
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
