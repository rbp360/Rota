from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import sys
import os
import traceback

# 1. ROOT PATH SETUP
# Force the backend to be visible
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

app = FastAPI()

# 2. EMERGENCY ROUTE (Always works)
@app.get("/api/health")
async def health_check():
    info = {
        "status": "online",
        "version": "1.8.3",
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
    except Exception as e:
        info["db"] = f"error: {str(e)}"
        info["trace"] = traceback.format_exc()
    
    return info

# 3. LAZY ROUTE LOAD
# We only load the complex stuff EXPLICITLY when needed
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

# 4. Standard App Exposure
# Vercel's ASGI builder will find this 'app'
app = app
