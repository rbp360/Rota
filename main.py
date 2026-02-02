from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(title="RotaAI Render API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global DB Handle to prevent re-initializing (saves memory/time)
_cached_db = None

# 1. ULTRA-FAST HEALTH (No DB allowed here)
@app.api_route("/", methods=["GET", "HEAD"])
def root():
    return {"status": "online", "version": "4.8.3", "engine": "stable"}

@app.get("/api/health")
def health():
    return {"status": "ok", "version": "4.8.3"}

def get_db_verified():
    global _cached_db
    if _cached_db:
        return _cached_db
        
    print("[DB] Initializing Firestore Client...")
    from google.cloud import firestore
    from google.oauth2 import service_account
    
    pk = os.getenv("FIREBASE_PRIVATE_KEY")
    email = os.getenv("FIREBASE_CLIENT_EMAIL")
    project_id = os.getenv("FIREBASE_PROJECT_ID")
    
    if not (pk and email and project_id):
        print("[DB] Missing Environment Variables")
        return None
        
    # Deep scrub the PK
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
    print("[DB] Connection Established.")
    return _cached_db

# 2. SEPARATE DB TEST (Run this manually in browser)
@app.get("/api/test-db")
def test_db():
    try:
        db = get_db_verified()
        if not db: return {"error": "Initialization failed"}
        # Fast write test
        db.collection("system").document("ping").set({"last_ping": firestore.SERVER_TIMESTAMP})
        return {"db": "connected", "write_test": "passed"}
    except Exception as e:
        return {"db": "failed", "error": str(e)}

@app.post("/api/import-staff")
async def handle_import(request: Request):
    try:
        data = await request.json()
        db = get_db_verified()
        if not db: return JSONResponse(status_code=500, content={"error": "DB Fail"})
        
        batch = db.batch()
        for i, s in enumerate(data):
            # Upsert logic
            staff_ref = db.collection("staff").document(str(s["id"]))
            batch.set(staff_ref, {"name": s["name"], "role": s.get("role", "Teacher")})
            if i % 10 == 0 and i > 0:
                batch.commit()
                batch = db.batch()
        batch.commit()
        return {"imported": len(data)}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/staff")
def get_staff():
    db = get_db_verified()
    if not db: return []
    docs = db.collection("staff").stream()
    return [{"name": d.to_dict().get("name"), "id": d.id} for d in docs]
