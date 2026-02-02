from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import sys
import os
import traceback

# 1. ROOT PATH SETUP
# Vercel's var/task is our root
root_dir = "/var/task"
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Also try the local path for dev
local_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if local_root not in sys.path:
    sys.path.insert(0, local_root)

app = FastAPI()

# 2. EMERGENCY HEALTH CHECK
@app.get("/api/health")
async def health_check():
    info = {
        "status": "online",
        "version": "1.9.0",
        "cwd": os.getcwd(),
        "sys_path": sys.path[:5]
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
        info["trace"] = traceback.format_exc()
    
    return info

# 3. BRIDGE TO REAL BACKEND
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
