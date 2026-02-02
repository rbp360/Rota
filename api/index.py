from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import sys
import os
import traceback

# FORCE PATH
root_dir = "/var/task"
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

app = FastAPI()

@app.get("/api/health")
async def health():
    info = {
        "status": "online",
        "version": "2.2.3",
        "db": "checking..."
    }
    try:
        from backend.database_firestore import get_db, FirestoreDB
        db = get_db()
        if db:
            info["db"] = "connected"
            info["staff_count"] = len(FirestoreDB.get_staff())
        else:
            info["db"] = "failed_init"
            info["db_error"] = os.environ.get("FIREBASE_INIT_ERROR")
    except Exception as e:
        info["db"] = f"error: {str(e)}"
        
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
