from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from . import database
from .database import engine, SessionLocal, Staff, Schedule, Absence, Cover, Setting
from .calendar_service import CalendarService
import pandas as pd
import os

from fastapi.middleware.cors import CORSMiddleware

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
    
    target_date = pd.to_datetime(date).date()
    
    # Check for existing absence for this staff member on this date
    existing_absence = db.query(Absence).filter(
        Absence.staff_id == staff.id,
        Absence.date == target_date
    ).first()
    
    if existing_absence:
        # Update periods if they changed, or just return existing
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
        
        # Get the absent teacher's schedule for this day to see which periods actually need cover
        absent_schedules = {sch.period: sch for sch in absent_staff.schedules if sch.day_of_week.lower() == day.lower()}
        
        # Only suggest cover for periods where the teacher is NOT free
        all_range_periods = list(range(absence.start_period, absence.end_period + 1))
        target_periods = [p for p in all_range_periods if p in absent_schedules and not absent_schedules[p].is_free]
        
        # Get all potential covering staff
        potential_staff = db.query(Staff).filter(Staff.is_active == True).all()
        available_profiles = []
        
        for s in potential_staff:
            if s.id == absent_staff.id:
                continue
                
            # Get free periods from their schedule
            free_periods = [sch.period for sch in s.schedules if sch.is_free and sch.day_of_week.lower() == day.lower()]
            
            # Get busy periods from their schedule
            busy_periods = {sch.period: sch.activity for sch in s.schedules if not sch.is_free and sch.day_of_week.lower() == day.lower()}

            # Remove periods where they have a calendar event, but keep track of what they are
            calendar_events = {}
            if s.calendar_url:
                try:
                    target_dt = pd.to_datetime(absence.date).date()
                    calendar_events = CalendarService.get_busy_periods(s.calendar_url, target_dt)
                    # Filter free_periods to only those truly free (no calendar event)
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
                "busy_periods": busy_periods, # Added this
                "calendar_events": calendar_events
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
def check_availability(periods: str, day: str = "Monday", date: str = None, db: Session = Depends(get_db)):
    try:
        period_list = [int(p) for p in periods.split(',') if p]
        
        # Check if any requested period is a formal teaching period (1-8)
        # Using 1-8 for periods. 
        # We assume Duties are 0, 9, 10, 11, 13 or similar outside range.
        has_teaching_periods = any(1 <= p <= 8 for p in period_list)
        
        query = db.query(Staff).filter(Staff.is_active == True)
        
        if has_teaching_periods:
            # If any teaching period is selected, only show staff who can cover periods
            query = query.filter(Staff.can_cover_periods == True)
            
        staff = query.all()
        
        # Use provided date or fallback to today
        if date:
            target_dt = pd.to_datetime(date).date()
        else:
            target_dt = pd.Timestamp.now().date()
            
        active_covers = db.query(Cover).join(Absence).filter(Absence.date == target_dt).all()
        
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
            
            # 3. Check their Outlook/ICS calendar
            calendar_busy = []
            if s.calendar_url:
                calendar_busy = CalendarService.get_busy_periods(s.calendar_url, target_dt)
            
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
                
                # check calendar
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
        # Fetch data summaries
        absences = db.query(Absence).all()
        covers = db.query(Cover).all()
        
        # Format data for AI context
        # We limit the data to avoid hitting context limits, though Gemini Flash is large.
        # Just sending the last 100 absences/covers should be enough for most reports.
        data_summary = "Staff Absences:\n"
        for a in absences[-100:]:
            data_summary += f"- Staff: {a.staff.name}, Date: {a.date}, Periods: {a.start_period}-{a.end_period}\n"
        
        data_summary += "\nCover Assignments:\n"
        for c in covers[-100:]:
             data_summary += f"- Covering Staff: {c.covering_staff.name}, Covered For: {c.absence.staff.name}, Date: {c.absence.date}, Period: {c.period}\n"
        
        report = ai_assistant.generate_report(query, data_summary)
        return {"report": report}
    except Exception as e:
        print(f"Report API Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
