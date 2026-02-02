from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os

# Ultra-simple app to prevent startup crashes
app = FastAPI(title="RotaAI Render API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. ROOT STATUS (Supports GET and HEAD for Render's monitor)
@app.api_route("/", methods=["GET", "HEAD"])
def root():
    return {"status": "online", "version": "4.8.2", "msg": "Stayin' Alive"}

def get_db_verified():
    from google.cloud import firestore
    from google.oauth2 import service_account
    
    pk = os.getenv("FIREBASE_PRIVATE_KEY")
    email = os.getenv("FIREBASE_CLIENT_EMAIL")
    project_id = os.getenv("FIREBASE_PROJECT_ID")
    
    if not (pk and email and project_id):
        return None
        
    # DEEP SCRUBBER for those line breaks
    # Join with \n and filter out any totally empty segments
    clean_pk = pk.strip().replace("\\n", "\n")
    lines = [line.strip() for line in clean_pk.split("\n") if line.strip()]
    final_pk = "\n".join(lines)
    
    creds = service_account.Credentials.from_service_account_info({
        "project_id": project_id,
        "private_key": final_pk,
        "client_email": email,
        "token_uri": "https://oauth2.googleapis.com/token",
        "type": "service_account"
    })
    return firestore.Client(credentials=creds, project=project_id)

@app.get("/api/health")
def health():
    info = {"status": "online", "version": "4.8.2"}
    try:
        db = get_db_verified()
        if db:
            info["db"] = "connected"
            # Fast check
            db.collection("staff").limit(1).get(timeout=5)
            info["verified"] = True
        else:
            info["db"] = "env_missing"
    except Exception as e:
        info["db_error"] = str(e)
    return info

@app.post("/api/import-staff")
async def handle_import(request: Request):
    try:
        data = await request.json()
        db = get_db_verified()
        if not db:
            return JSONResponse(status_code=500, content={"error": "DB Init Fail"})
        
        batch = db.batch()
        for i, s in enumerate(data):
            staff_ref = db.collection("staff").document(str(s["id"]))
            batch.set(staff_ref, {
                "name": s["name"],
                "role": s.get("role", "Teacher"),
                "is_active": True
            })
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
