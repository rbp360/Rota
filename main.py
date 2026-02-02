from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import os
import requests
import json
import time

app = FastAPI()

# 1. LIGHTWEIGHT CONFIG
PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID")

@app.api_route("/", methods=["GET", "HEAD"])
def root():
    return {"status": "online", "version": "5.1.0", "msg": "REST Engine - Stable!"}

@app.get("/api/health")
def health():
    return {"status": "ok", "version": "5.1.0"}

# 2. REST DATABASE LOGIC (No libraries needed)
def rest_save_doc(collection, doc_id, data):
    """Saves a document using the Google Firestore REST API."""
    url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/{collection}/{doc_id}"
    
    # Firestore REST requires a specific JSON structure for fields
    # We will use a simplified version for this migration
    payload = {"fields": {}}
    for k, v in data.items():
        if isinstance(v, bool): payload["fields"][k] = {"booleanValue": v}
        elif isinstance(v, int): payload["fields"][k] = {"integerValue": str(v)}
        else: payload["fields"][k] = {"stringValue": str(v)}
            
    try:
        # We use PATCH so it creates OR updates (upsert)
        r = requests.patch(url, json=payload, timeout=10)
        return r.status_code == 200
    except:
        return False

@app.post("/api/import-staff")
async def handle_import(request: Request):
    try:
        teachers = await request.json()
        saved_count = 0
        
        for t in teachers:
            # 1. Save main staff record
            success = rest_save_doc("staff", str(t["id"]), {
                "name": t["name"],
                "role": t.get("role", "Teacher"),
                "is_active": True
            })
            
            # 2. Save schedules (simplified for REST)
            if success and "schedules" in t:
                for sch in t["schedules"][:5]: # Limit to first 5 to prevent timeouts
                    rest_save_doc(f"staff/{t['id']}/schedules", f"{sch['day_of_week']}_{sch['period']}", {
                        "day": sch["day_of_week"],
                        "period": sch["period"],
                        "is_free": sch["is_free"]
                    })
            
            if success: saved_count += 1
            # Throttling to prevent Render killing the app for high CPU
            time.sleep(0.1) 
            
        return {"imported": saved_count, "status": "success"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/staff")
def get_staff():
    url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/staff"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            docs = data.get("documents", [])
            return [{"id": d["name"].split("/")[-1], "name": d["fields"].get("name", {}).get("stringValue")} for d in docs]
    except: pass
    return []
