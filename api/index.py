from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import sys
import os
import traceback

# Force root path for backend folder
root_dir = "/var/task"
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

app = FastAPI()

@app.get("/api/health")
async def health():
    info = {
        "status": "online",
        "version": "2.1.0",
        "backend": "checking..."
    }
    try:
        from backend.database_firestore import get_db, FirestoreDB
        db = get_db()
        if db:
            info["backend"] = "connected"
            info["staff_count"] = len(FirestoreDB.get_staff())
        else:
            info["backend"] = "init_failed"
    except Exception as e:
        info["backend"] = f"error: {str(e)}"
        
    return info

@app.post("/api/import-staff")
async def handle_import(request: Request):
    try:
        from backend.main_firestore import import_staff_bridge
        return await import_staff_bridge(request)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "trace": traceback.format_exc()}
        )

# EXPORT
app = app
