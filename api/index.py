from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import sys
import os
import traceback

# Root path for backend folder
root_dir = "/var/task"
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

app = FastAPI(title="RotaAI School API")

@app.get("/api/health")
async def health():
    db_status = "idle"
    # We do NOT import database here to keep the health check ultra fast.
    return {
        "status": "online",
        "version": "2.2.0",
        "db": db_status,
        "note": "School Rota API is live. Run push_to_cloud.py to sync data."
    }

@app.post("/api/import-staff")
async def handle_import(request: Request):
    try:
        # Complex imports happen ONLY here
        from backend.main_firestore import import_staff_bridge
        return await import_staff_bridge(request)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "trace": traceback.format_exc()}
        )

# Catch-all to help with routing
@app.get("/api/{path:path}")
async def catch_all(path: str):
    return {"message": f"Endpoint '/api/{path}' reached. Use /api/health for status."}

# Standard export
app = app
