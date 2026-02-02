from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import sys

# Add root for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "status": "online",
        "version": "4.6.0",
        "msg": "Logic Re-introduced. Checking database..."
    }

@app.get("/api/health")
def health():
    info = {"status": "ok", "version": "4.6.0"}
    try:
        from backend.database_firestore import get_db
        db = get_db()
        if db:
            info["db"] = "connected"
            # Attempt a tiny read to verify the key
            db.collection("staff").limit(1).get()
            info["db_auth"] = "verified"
        else:
            info["db"] = "not_connected"
            info["db_error"] = os.getenv("FIREBASE_INIT_ERROR", "Unknown init error")
    except Exception as e:
        info["db"] = f"crash: {str(e)}"
    return info

@app.post("/api/import-staff")
async def handle_import(request: Request):
    try:
        data = await request.json()
        from backend.database_firestore import get_db
        db = get_db()
        if not db:
            return JSONResponse(status_code=500, content={"error": "Database not connected."})
        
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
        return JSONResponse(status_code=500, content={"error": str(e)})

# Core listing endpoint
@app.get("/api/staff")
def get_staff():
    from backend.database_firestore import FirestoreDB
    return FirestoreDB.get_staff()
