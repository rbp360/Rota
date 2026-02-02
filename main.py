from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import os

app = FastAPI()

# Global variable to hold the DB connection
_db = None

@app.api_route("/", methods=["GET", "HEAD"])
def root():
    return {"status": "online", "version": "4.8.5", "mode": "memory-optimized"}

@app.get("/api/health")
def health():
    return {"status": "ok", "version": "4.8.5"}

def get_db():
    global _db
    if _db: return _db
    
    print("[DB] First-time connection...")
    from google.cloud import firestore
    from google.oauth2 import service_account
    
    pk = os.getenv("FIREBASE_PRIVATE_KEY", "").strip()
    email = os.getenv("FIREBASE_CLIENT_EMAIL", "").strip()
    project_id = os.getenv("FIREBASE_PROJECT_ID", "").strip()
    
    if not pk or not email:
        print("[DB] ERROR: Environment variables missing")
        return None
        
    # Standard clean for Python
    clean_pk = pk.replace("\\n", "\n").strip('"').strip("'")
    
    try:
        creds = service_account.Credentials.from_service_account_info({
            "project_id": project_id,
            "private_key": clean_pk,
            "client_email": email,
            "token_uri": "https://oauth2.googleapis.com/token",
            "type": "service_account"
        })
        _db = firestore.Client(credentials=creds, project=project_id)
        print("[DB] SUCCESS: Client ready")
        return _db
    except Exception as e:
        print(f"[DB] CRASH: {e}")
        return None

@app.get("/api/test-db")
def test_db():
    db = get_db()
    if not db: return {"status": "fail", "msg": "Could not init"}
    try:
        # Simplest possible check: list collections (very low memory)
        collections = db.collections()
        return {"status": "connected", "collections_found": True}
    except Exception as e:
        return {"status": "error", "msg": str(e)}

@app.post("/api/import-staff")
async def handle_import(request: Request):
    try:
        data = await request.json()
        db = get_db()
        if not db: return JSONResponse(status_code=500, content={"error": "db_fail"})
        
        # Batch write is MANDATORY for memory efficiency
        batch = db.batch()
        for i, s in enumerate(data):
            ref = db.collection("staff").document(str(s["id"]))
            batch.set(ref, {"name": s["name"], "role": s.get("role", "Teacher")})
            
            # Commit every 5 items to keep memory spike low
            if (i + 1) % 5 == 0:
                batch.commit()
                batch = db.batch()
        
        batch.commit()
        return {"imported": len(data)}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/staff")
def get_staff():
    db = get_db()
    if not db: return []
    try:
        # Limited stream to save memory
        docs = db.collection("staff").limit(10).stream()
        return [{"id": d.id, "name": d.to_dict().get("name")} for d in docs]
    except: return []
