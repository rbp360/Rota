from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import traceback

app = FastAPI(title="RotaAI Render API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_lean_db():
    print("[DB] Attempting lean connection...")
    from google.cloud import firestore
    from google.oauth2 import service_account
    
    pk = os.getenv("FIREBASE_PRIVATE_KEY")
    email = os.getenv("FIREBASE_CLIENT_EMAIL")
    project_id = os.getenv("FIREBASE_PROJECT_ID")
    
    if not (pk and email and project_id):
        print("[DB] Missing basic env variables")
        return None
        
    try:
        # SUPER CLEANER
        # 1. Strip all potential literal quotes
        clean_pk = pk.strip().strip('"').strip("'")
        
        # 2. If it contains literal \n (backslash + n), replace it
        if "\\n" in clean_pk:
            clean_pk = clean_pk.replace("\\n", "\n")
            
        # 3. Final verification - join lines to remove accidental empty ones
        lines = [l.strip() for l in clean_pk.split("\n") if l.strip()]
        clean_pk = "\n".join(lines)
        
        if "-----BEGIN PRIVATE KEY-----" not in clean_pk:
            print("[DB] Key header missing from cleaned string")
            return None
            
        creds = service_account.Credentials.from_service_account_info({
            "project_id": project_id,
            "private_key": clean_pk,
            "client_email": email,
            "token_uri": "https://oauth2.googleapis.com/token",
            "type": "service_account"
        })
        db = firestore.Client(credentials=creds, project=project_id)
        print("[DB] Client created successfully")
        return db
    except Exception as e:
        print(f"[DB] Crash during auth setup: {e}")
        return None

@app.get("/")
def root():
    return {"status": "online", "version": "4.8.1", "msg": "Standalone Logic"}

@app.get("/api/health")
def health():
    info = {"status": "online", "version": "4.8.1"}
    try:
        db = get_lean_db()
        if db:
            info["db_init"] = "success"
            # Tiny network probe
            try:
                db.collection("staff").limit(1).get(timeout=10)
                info["db_net"] = "verified"
            except Exception as net_e:
                info["db_net"] = f"Network Check Failed: {str(net_e)}"
        else:
            info["db_init"] = "failed"
    except Exception as e:
        info["crash"] = str(e)
    return info

@app.post("/api/import-staff")
async def handle_import(request: Request):
    try:
        data = await request.json()
        db = get_lean_db()
        if not db:
            return JSONResponse(status_code=500, content={"error": "Database could not initialize."})
        
        count = 0
        batch = db.batch()
        for i, s in enumerate(data):
            staff_ref = db.collection("staff").document(str(s["id"]))
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
            if "schedules" in s:
                for sch in s["schedules"]:
                    batch.set(staff_ref.collection("schedules").document(f"{sch['day_of_week']}_{sch['period']}"), sch)
            count += 1
            if i % 10 == 0 and i > 0:
                batch.commit()
                batch = db.batch()
        batch.commit()
        return {"imported": count}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e), "trace": traceback.format_exc()})

@app.get("/api/staff")
def get_staff():
    db = get_lean_db()
    if not db: return []
    try:
        docs = db.collection("staff").stream()
        return [{**doc.to_dict(), "id": doc.id} for doc in docs]
    except: return []
