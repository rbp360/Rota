from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import os
import requests
import json

app = FastAPI()

# 1. CORE CONFIG
PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID")

@app.api_route("/", methods=["GET", "HEAD"])
def root():
    return {"status": "online", "version": "4.9.1", "engine": "lightweight-rest"}

@app.get("/api/health")
def health():
    return {"status": "ok", "project": PROJECT_ID, "version": "4.9.1"}

@app.get("/api/test-db")
def test_db():
    if not PROJECT_ID: return {"error": "Missing PROJECT_ID"}
    # Direct public ping to Google's REST API
    url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/staff?pageSize=1"
    try:
        resp = requests.get(url, timeout=10)
        return {"status": "rest-probe", "code": resp.status_code, "msg": "Website can reach Google!"}
    except Exception as e:
        return {"status": "timeout", "error": str(e)}

@app.post("/api/import-staff")
async def handle_import(request: Request):
    try:
        teachers = await request.json()
        print(f"STABILITY TEST: Received {len(teachers)} teachers.")
        return {"status": "received", "count": len(teachers), "note": "REST Gateway is STABLE"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/staff")
def get_staff():
    return {"msg": "REST API Mode Active."}
