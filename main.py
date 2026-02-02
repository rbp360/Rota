from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import os
import requests
import json
import time

app = FastAPI()

# 1. CORE CONFIG
PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID")
CLIENT_EMAIL = os.getenv("FIREBASE_CLIENT_EMAIL")
PRIVATE_KEY = os.getenv("FIREBASE_PRIVATE_KEY")

@app.api_route("/", methods=["GET", "HEAD"])
def root():
    return {"status": "online", "version": "4.9.0", "engine": "lightweight-rest"}

@app.get("/api/health")
def health():
    return {"status": "ok", "project": PROJECT_ID}

# 2. LIGHTWEIGHT FIRESTORE ACCESS (No heavy libraries)
def firestore_request(method, path, data=None):
    """Hits the Firestore REST API directly."""
    url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/{path}"
    
    # Simple write for import
    if method == "POST":
        resp = requests.patch(url, json={"fields": data} if data else {}, params={"updateMask.fieldPaths": list(data.keys()) if data else []})
        return resp.status_code
    
    # Simple read
    resp = requests.get(url)
    return resp.json() if resp.status_code == 200 else None

@app.get("/api/test-db")
def test_db():
    if not PROJECT_ID: return {"error": "Missing PROJECT_ID"}
    # Just try to fetch the staff collection metadata
    url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/staff?pageSize=1"
    resp = requests.get(url)
    return {"status": "rest-connected", "code": resp.status_code, "msg": "Auth not even needed for public probe"}

@app.post("/api/import-staff")
async def handle_import(request: Request):
    try:
        teachers = await request.json()
        # For simplicity in this REST version, we just verify we got the data
        # Real REST batching is complex, so we'll just log success for now
        # until the server is stable.
        print(f"Received {len(teachers)} teachers for import.")
        return {"status": "received", "count": len(teachers), "note": "Server stable! Ready for full logic."}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/staff")
def get_staff():
    return {"msg": "REST API Mode Active. Use /api/health to verify connectivity."}
