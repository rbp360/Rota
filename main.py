from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import os

app = FastAPI()

@app.get("/")
def root():
    return {
        "status": "online",
        "version": "4.6.1",
        "msg": "Minimal Firestore Build"
    }

@app.get("/api/health")
def health():
    info = {"status": "ok", "version": "4.6.1"}
    try:
        from google.cloud import firestore
        from google.oauth2 import service_account
        
        pk = os.getenv("FIREBASE_PRIVATE_KEY")
        email = os.getenv("FIREBASE_CLIENT_EMAIL")
        project_id = os.getenv("FIREBASE_PROJECT_ID")
        
        if pk and email and project_id:
            raw_pk = pk.strip().replace('"', '').replace("'", "")
            clean_pk = raw_pk.replace("\\n", "\n")
            lines = [l.strip() for l in clean_pk.split("\n") if l.strip()]
            clean_pk = "\n".join(lines)
            
            info["key_preview"] = clean_pk[:25] + "..."
            
            creds = service_account.Credentials.from_service_account_info({
                "project_id": project_id,
                "private_key": clean_pk,
                "client_email": email,
                "token_uri": "https://oauth2.googleapis.com/token",
                "type": "service_account"
            })
            db = firestore.Client(credentials=creds, project=project_id)
            db.collection("staff").limit(1).get()
            info["db"] = "connected_and_verified"
        else:
            info["db"] = "missing_env"
    except Exception as e:
        info["db"] = "error"
        info["error"] = str(e)
    return info

@app.post("/api/import-staff")
async def handle_import(request: Request):
    try:
        data = await request.json()
        from google.cloud import firestore
        from google.oauth2 import service_account
        
        pk = os.getenv("FIREBASE_PRIVATE_KEY")
        email = os.getenv("FIREBASE_CLIENT_EMAIL")
        project_id = os.getenv("FIREBASE_PROJECT_ID")
        
        raw_pk = pk.strip().replace('"', '').replace("'", "")
        clean_pk = raw_pk.replace("\\n", "\n")
        lines = [l.strip() for l in clean_pk.split("\n") if l.strip()]
        clean_pk = "\n".join(lines)
        
        creds = service_account.Credentials.from_service_account_info({
            "project_id": project_id,
            "private_key": clean_pk,
            "client_email": email,
            "token_uri": "https://oauth2.googleapis.com/token",
            "type": "service_account"
        })
        db = firestore.Client(credentials=creds, project=project_id)
        
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
