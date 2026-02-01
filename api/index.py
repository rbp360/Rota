from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import sys
import os
import traceback

# 1. FORCE THE PATH
# This ensures that even in 'Serverless' mode, the backend folder is found.
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

app = FastAPI()

# 2. STANDALONE HEALTH CHECK (No imports required)
# If this works, the plumbing is correct.
@app.get("/api/health")
async def health_check():
    db_status = "not_checked"
    staff_count = 0
    
    # Try to get the real data, but don't crash if it fails
    try:
        from backend.database_firestore import get_db, FirestoreDB
        db = get_db()
        if db:
            db_status = "connected"
            staff_count = len(FirestoreDB.get_staff())
        else:
            db_status = "db_init_failed"
    except Exception as e:
        db_status = f"import_error: {str(e)}"
        
    return {
        "status": "online",
        "version": "1.5.2",
        "db": db_status,
        "staff_count": staff_count,
        "note": "If you see this, the API is ALIVE."
    }

# 3. BRIDGE TO REAL BACKEND
@app.post("/api/import-staff")
async def bridge_import(request: Request):
    try:
        from backend.main_firestore import import_staff_bridge
        return await import_staff_bridge(request)
    except Exception as e:
        return {"error": f"Bridge failed: {str(e)}"}

# Mandatory for Vercel
handler = app
