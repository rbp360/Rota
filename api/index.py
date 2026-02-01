from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import sys
import os
import traceback

# 1. Ensure the 'backend' folder is findable
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root not in sys.path:
    sys.path.insert(0, root)

app = FastAPI()

# 2. Try to import the real app logic
try:
    from backend.main_firestore import app as backend_app
    # Use the real backend app
    app = backend_app
except Exception as e:
    # If it fails, we keep our dummy app to report the error visually
    error_detail = str(e)
    error_trace = traceback.format_exc()
    
    @app.get("/api/health")
    async def health_failure():
        return {
            "status": "backend_load_failed",
            "error": error_detail,
            "trace": error_trace
        }

# 3. Add a top-level health check (Vercel heart-beat)
@app.get("/api/health")
async def health_check():
    db_status = "unknown"
    staff_count = 0
    try:
        from backend.database_firestore import get_db, FirestoreDB
        db = get_db()
        db_status = "connected" if db else "failed"
        if db:
            staff_count = len(FirestoreDB.get_staff())
    except:
        pass
        
    return {
        "status": "ok",
        "version": "1.5.0",
        "db": db_status,
        "staff_count": staff_count,
        "environment": "vercel"
    }

# Vercel looks for 'app'
app = app
