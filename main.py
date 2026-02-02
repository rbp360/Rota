from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
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

# 1. SERVE FRONTEND (If exists)
frontend_path = os.path.join(os.path.dirname(__file__), "frontend", "dist")
if os.path.exists(frontend_path):
    # Mount assets folder
    assets_path = os.path.join(frontend_path, "assets")
    if os.path.exists(assets_path):
        app.mount("/assets", StaticFiles(directory=assets_path), name="assets")
    
    # Simple root response for HEAD monitor, but GET returns index.html
    @app.api_route("/", methods=["GET", "HEAD"])
    async def serve_frontend(request: Request):
        if request.method == "HEAD":
            return {"status": "online"}
        index_file = os.path.join(frontend_path, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"status": "online", "msg": "index.html not found"}

# 2. HEALTH & STATUS
@app.get("/api/health")
def health():
    return {"status": "ok", "version": "5.5.0", "engine": "production"}

# 3. STAFF ENDPOINTS
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

# 4. ABSENCE & ROTA
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
    aid = FirestoreDB.add_absence(staff["id"], staff["name"], target_date, start_period, end_period)
    return {"id": aid, "status": "created"}

# 5. COVER SYSTEM
@app.get("/api/suggest-cover/{absence_id}")
async def suggest_cover(absence_id: str, day: str = "Monday"):
    try:
        from backend.database_firestore import FirestoreDB
        from backend.ai_agent import RotaAI
        absences = FirestoreDB.get_absences()
        absence = next((a for a in absences if a["id"] == absence_id), None)
        if not absence: raise HTTPException(status_code=404, detail="Absence not found")
        
        all_staff = FirestoreDB.get_staff()
        absent_staff_id = absence["staff_id"]
        
        available_profiles = []
        for s in all_staff:
            if s["id"] == absent_staff_id: continue
            s_schedules = FirestoreDB.get_schedules(s["id"], day=day)
            available_profiles.append({
                "name": s["name"], "role": s.get("role", "Teacher"),
                "is_priority": s.get("is_priority", False),
                "is_specialist": s.get("is_specialist", False),
                "free_periods": [sch["period"] for sch in s_schedules if sch.get("is_free", False)],
                "busy_periods": {sch["period"]: sch.get("activity", "Class") for sch in s_schedules if not sch.get("is_free", False)}
            })

        ai = RotaAI()
        ai_response = ai.suggest_cover(
            absent_staff=absence["staff_name"], day=day,
            periods=[absence["start_period"]],
            available_staff_profiles=available_profiles
        )
        return {"suggestions": ai_response}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/api/assign-cover")
def assign_cover(absence_id: str, staff_name: str, periods: str):
    from backend.database_firestore import FirestoreDB
    success = FirestoreDB.assign_cover(absence_id, staff_name, periods)
    if success: return {"status": "assigned"}
    raise HTTPException(status_code=500, detail="Assignment failed")

@app.delete("/api/unassign-cover")
def unassign_cover(absence_id: str, period: int):
    from backend.database_firestore import FirestoreDB
    success = FirestoreDB.unassign_cover(absence_id, period)
    if success: return {"status": "unassigned"}
    raise HTTPException(status_code=500, detail="Unassignment failed")

# 6. REPORTING & AI
@app.get("/api/generate-report")
def generate_report(query: str):
    try:
        from backend.database_firestore import FirestoreDB
        from backend.ai_agent import RotaAI
        absences = FirestoreDB.get_absences()
        context = "Recent Absences and Covers:\n"
        for a in absences[-20:]:
            context += f"- {a['date']}: {a['staff_name']} (Periods {a['start_period']}-{a['end_period']})\n"
            for c in a.get("covers", []):
                context += f"  - Period {c['period']} covered by {c['staff_name']}\n"
        
        ai = RotaAI()
        report = ai.generate_report(query, context)
        return {"report": report}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# 7. UTILITIES
@app.get("/api/availability")
def check_availability(periods: str, day: str = "Monday", date: str = None):
    from backend.database_firestore import FirestoreDB
    all_staff = FirestoreDB.get_staff()
    plist = [int(p) for p in periods.split(',') if p]
    available = []
    for s in all_staff:
        if not s.get("is_active", True): continue
        sches = FirestoreDB.get_schedules(s["id"], day=day)
        free_p = [sch["period"] for sch in sches if sch.get("is_free", False)]
        if all(p in free_p for p in plist):
            available.append({"name": s["name"], "is_free": True})
    return available

@app.post("/api/import-staff")
async def handle_import(request: Request):
    from backend.main_firestore import import_staff_bridge
    return await import_staff_bridge(request)
