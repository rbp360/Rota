from fastapi import FastAPI, Request, HTTPException
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

# Global DB to preserve memory
_cached_db = None

# 1. ROOT & HEALTH (Supports GET and HEAD for Render)
@app.api_route("/", methods=["GET", "HEAD"])
def root():
    return {
        "status": "online", 
        "message": "RotaAI is running on Render!", 
        "version": "5.0.0",
        "hint": "Check /api/health for DB status"
    }

@app.get("/api/health")
def health():
    return {"status": "ok", "version": "5.0.0", "engine": "production"}

def get_db_verified():
    global _cached_db
    if _cached_db: return _cached_db
    
    from google.cloud import firestore
    from google.oauth2 import service_account
    
    pk = os.getenv("FIREBASE_PRIVATE_KEY")
    email = os.getenv("FIREBASE_CLIENT_EMAIL")
    project_id = os.getenv("FIREBASE_PROJECT_ID")
    
    if not (pk and email and project_id): return None
        
    # Scrubber for the line-break issue
    clean_pk = pk.strip().replace("\\n", "\n")
    lines = [l.strip() for l in clean_pk.split("\n") if l.strip()]
    final_pk = "\n".join(lines)
    
    creds = service_account.Credentials.from_service_account_info({
        "project_id": project_id,
        "private_key": final_pk,
        "client_email": email,
        "token_uri": "https://oauth2.googleapis.com/token",
        "type": "service_account"
    })
    _cached_db = firestore.Client(credentials=creds, project=project_id)
    return _cached_db

# 2. IMPORT DATA BRIDGE (Full Logic)
@app.post("/api/import-staff")
async def handle_import(request: Request):
    try:
        data = await request.json()
        db = get_db_verified()
        if not db: return JSONResponse(status_code=500, content={"error": "DB Fail"})
        
        count = 0
        batch = db.batch()
        for i, s in enumerate(data):
            staff_ref = db.collection("staff").document(str(s["id"]))
            batch.set(staff_ref, {
                "name": s["name"],
                "role": s.get("role", "Teacher"),
                "profile": s.get("profile"),
                "is_active": True
            })
            if "schedules" in s:
                for sch in s["schedules"]:
                    batch.set(staff_ref.collection("schedules").document(f"{sch['day_of_week']}_{sch['period']}"), sch)
            count += 1
            if count % 10 == 0:
                batch.commit()
                batch = db.batch()
        batch.commit()
        return {"imported": count}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# 3. CORE API ROUTES
@app.get("/api/staff")
def get_all_staff():
    from backend.database_firestore import FirestoreDB
    return FirestoreDB.get_staff()

@app.get("/api/daily-rota")
def get_daily_rota(date: str):
    from backend.database_firestore import FirestoreDB
    from dateutil import parser
    target_date = parser.parse(date).strftime('%Y-%m-%d')
    return FirestoreDB.get_absences(date=target_date)

@app.get("/api/suggest-cover/{absence_id}")
async def suggest_cover(absence_id: str, day: str = "Monday"):
    try:
        from backend.database_firestore import FirestoreDB
        from backend.ai_agent import RotaAI
        absences = FirestoreDB.get_absences()
        absence = next((a for a in absences if a["id"] == absence_id), None)
        if not absence: raise HTTPException(status_code=404, detail="Absence not found")
        
        ai = RotaAI()
        all_staff = FirestoreDB.get_staff()
        available_profiles = []
        for s in all_staff:
            if s["id"] == absence["staff_id"]: continue
            s_schedules = FirestoreDB.get_schedules(s["id"], day=day)
            available_profiles.append({
                "name": s["name"], "role": s.get("role", "Teacher"),
                "is_priority": s.get("is_priority", False),
                "free_periods": [sch["period"] for sch in s_schedules if sch["is_free"]]
            })

        ai_response = ai.suggest_cover(
            absent_staff=absence["staff_name"], day=day,
            periods=[absence["start_period"]],
            available_staff_profiles=available_profiles
        )
        return {"suggestions": ai_response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
