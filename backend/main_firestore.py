from fastapi import FastAPI, Depends, HTTPException, Query
from .database_firestore import FirestoreDB
from .calendar_service import CalendarService
from datetime import datetime, date
from dateutil import parser
from fastapi.middleware.cors import CORSMiddleware
from .ai_agent import RotaAI
import os

app = FastAPI(title="Teacher Cover Rota API (Firestore)")

# In production, this should be more restrictive
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ai_assistant = RotaAI()

@app.get("/")
def read_root():
    return {"message": "Teacher Cover Rota API (Firestore) is running"}

@app.get("/staff")
def get_staff():
    return FirestoreDB.get_staff()

@app.post("/absences")
def log_absence(staff_name: str, date: str, start_period: int, end_period: int):
    staff = FirestoreDB.get_staff_member(name=staff_name)
    if not staff:
        raise HTTPException(status_code=404, detail=f"Staff '{staff_name}' not found")
    
    # In Firestore, we use string dates "YYYY-MM-DD"
    target_date = parser.parse(date).strftime('%Y-%m-%d')
    absence_id = FirestoreDB.add_absence(staff["id"], staff["name"], target_date, start_period, end_period)
    return {"id": absence_id, "status": "created"}

@app.get("/suggest-cover/{absence_id}")
def suggest_cover(absence_id: int, day: str = "Monday"):
    # Note: Firestore IDs are strings, but the API might still receive ints from legacy frontend
    # We should handle both or transition frontend to string IDs
    abs_id_str = str(absence_id)
    try:
        absences = FirestoreDB.get_absences()
        absence = next((a for a in absences if a["id"] == abs_id_str), None)
        
        if not absence:
            raise HTTPException(status_code=404, detail="Absence not found")
        
        absent_staff_id = absence["staff_id"]
        all_staff = FirestoreDB.get_staff()
        absent_staff = next((s for s in all_staff if s["id"] == absent_staff_id), None)
        
        # Get absent staff schedules
        absent_schedules = FirestoreDB.get_schedules(absent_staff_id, day=day)
        absent_sched_map = {sch["period"]: sch for sch in absent_schedules if not sch["is_free"]}
        
        all_range_periods = list(range(absence["start_period"], absence["end_period"] + 1))
        target_periods = [p for p in all_range_periods if p in absent_sched_map]
        
        available_profiles = []
        for s in all_staff:
            if s["id"] == absent_staff_id:
                continue
            
            s_schedules = FirestoreDB.get_schedules(s["id"], day=day)
            free_periods = [sch["period"] for sch in s_schedules if sch["is_free"]]
            busy_periods = {sch["period"]: sch["activity"] for sch in s_schedules if not sch["is_free"]}

            calendar_events = {}
            if s.get("calendar_url"):
                try:
                    target_dt = parser.parse(absence["date"]).date()
                    calendar_events = CalendarService.get_busy_periods(s["calendar_url"], target_dt)
                    free_periods = [p for p in free_periods if p not in calendar_events]
                except Exception:
                    pass

            available_profiles.append({
                "name": s["name"],
                "role": s.get("role", "Teacher"),
                "can_cover_periods": s.get("can_cover_periods", True),
                "profile": s.get("profile"),
                "is_priority": s.get("is_priority", False),
                "is_specialist": s.get("is_specialist", False),
                "free_periods": free_periods,
                "busy_periods": busy_periods,
                "calendar_events": calendar_events
            })

        ai_response = ai_assistant.suggest_cover(
            absent_staff=absence["staff_name"],
            day=day,
            periods=target_periods,
            available_staff_profiles=available_profiles
        )
        
        return {
            "absence_id": absence_id,
            "absent_teacher": absence["staff_name"],
            "day": day,
            "periods": target_periods,
            "suggestions": ai_response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/availability")
def check_availability(periods: str, day: str = "Monday", date: str = None):
    try:
        period_list = [int(p) for p in periods.split(',') if p]
        has_teaching_periods = any(1 <= p <= 8 for p in period_list)
        
        all_staff = FirestoreDB.get_staff()
        if has_teaching_periods:
            staff = [s for s in all_staff if s.get("is_active", True) and s.get("can_cover_periods", True)]
        else:
            staff = [s for s in all_staff if s.get("is_active", True)]
            
        if date:
            target_dt = parser.parse(date).strftime('%Y-%m-%d')
        else:
            target_dt = datetime.now().strftime('%Y-%m-%d')
            
        active_absences = FirestoreDB.get_absences(date=target_dt)
        cover_map = {} # covering_staff_id -> {period: absent_staff_name}
        for a in active_absences:
            for c in a.get("covers", []):
                sid = c["covering_staff_id"]
                if sid not in cover_map:
                    cover_map[sid] = {}
                cover_map[sid][c["period"]] = a["staff_name"]

        results = []
        for s in staff:
            s_schedules = FirestoreDB.get_schedules(s["id"], day=day)
            day_schedules = {sch["period"]: sch for sch in s_schedules}
            staff_covers = cover_map.get(s["id"], {})
            
            calendar_busy = []
            if s.get("calendar_url"):
                try:
                    dt_obj = parser.parse(target_dt).date()
                    calendar_busy = CalendarService.get_busy_periods(s["calendar_url"], dt_obj)
                except:
                    pass
            
            is_all_free = True
            first_busy_reason = None

            for p in period_list:
                is_timetable_free = day_schedules.get(p) and day_schedules[p]["is_free"]
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
                    first_busy_reason = day_schedules[p].get("activity", "Busy") if day_schedules.get(p) else "Busy"
                    break
            
            if is_all_free:
                display_activity = "Free"
                if not s.get("is_specialist", False):
                    reasons = []
                    for p in period_list:
                        act = day_schedules.get(p, {}).get("activity", "")
                        if act and act.lower() not in ['free', 'none', 'available', '']:
                            reasons.append(act)
                    if reasons:
                        display_activity = f"class doing {', '.join(reasons)}" if len(reasons) == 1 else "Various Activities"

                results.append({
                    "name": s["name"], 
                    "profile": s.get("profile"), 
                    "is_priority": s.get("is_priority", False),
                    "is_specialist": s.get("is_specialist", False),
                    "is_free": True,
                    "activity": display_activity
                })
            elif s.get("is_specialist", False):
                results.append({
                    "name": s["name"], 
                    "profile": s.get("profile"), 
                    "is_priority": s.get("is_priority", False),
                    "is_specialist": True,
                    "is_free": False,
                    "activity": first_busy_reason
                })
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/assign-cover")
def assign_cover(absence_id: str, staff_name: str, periods: str):
    staff = FirestoreDB.get_staff_member(name=staff_name)
    if not staff:
        raise HTTPException(status_code=404, detail="Cover staff not found")
    
    period_list = [int(p) for p in periods.split(',') if p]
    for p in period_list:
        FirestoreDB.assign_cover(str(absence_id), staff["id"], staff["name"], p)
    
    return {"message": f"Assigned {staff_name} to periods {periods}"}

@app.get("/daily-rota")
def get_daily_rota(date: str):
    try:
        target_date = parser.parse(date).strftime('%Y-%m-%d')
        absences = FirestoreDB.get_absences(date=target_date)
        
        results = []
        for a in absences:
            covers = []
            for c in a.get("covers", []):
                covers.append({
                    "period": c["period"],
                    "covering_staff_name": c["covering_staff_name"]
                })
            
            results.append({
                "absence_id": a["id"],
                "staff_name": a["staff_name"],
                "start_period": a["start_period"],
                "end_period": a["end_period"],
                "covers": covers
            })
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/unassign-cover")
def unassign_cover(absence_id: str, period: int):
    FirestoreDB.unassign_cover(str(absence_id), period)
    return {"message": f"Unassigned period {period}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
