from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import sys
import os
import traceback

# Add project root
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Initialize app variable
app = None

try:
    from backend.main_firestore import app as backend_app
    app = backend_app
    
    # Add health check to the real app
    @app.get("/api/health")
    async def health_check():
        db_status = "unknown"
        staff_count = 0
        try:
            from backend.database_firestore import get_db, FirestoreDB
            db = get_db()
            db_status = "connected" if db else "failed"
            if db: staff_count = len(FirestoreDB.get_staff())
        except: pass
        
        return {
            "status": "ok",
            "version": "1.3.5",
            "db": db_status,
            "staff_count": staff_count,
            "environment": "vercel"
        }
except Exception as e:
    # EMERGENCY FALLBACK APP
    app = FastAPI()
    error_msg = str(e)
    trace = traceback.format_exc()
    
    @app.all("/api/{path:path}")
    async def catch_all(request: Request, path: str):
        return JSONResponse(
            status_code=500,
            content={
                "status": "initialization_failed",
                "version": "1.3.5-error",
                "error": error_msg,
                "trace": trace,
            }
        )

# EXPORT MANDATORY FOR VERCEL
handler = app
