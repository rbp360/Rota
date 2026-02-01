from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import sys
import os
import traceback

# Add the project root to the path so we can find the 'backend' folder
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.append(root_dir)

try:
    from backend.main_firestore import app
except Exception as e:
    # If the app fails to import, create a dummy app to report the error
    app = FastAPI()
    error_msg = str(e)
    stack_trace = traceback.format_exc()
    
    @app.get("/api/health")
    async def health_error():
        return {
            "status": "initialization_failed",
            "error": error_msg,
            "trace": stack_trace,
            "cwd": os.getcwd(),
            "sys_path": sys.path
        }

    @app.get("/api/{path:path}")
    async def report_error(path: str):
        return JSONResponse(
            status_code=500,
            content={
                "error": "Backend Initialization Failed",
                "detail": error_msg,
                "trace": stack_trace
            }
        )

# Add a health check at the very top level (if app imported successfully)
try:
    @app.get("/api/health")
    async def health():
        db_status = "unknown"
        try:
            from backend.database_firestore import get_db
            db = get_db()
            db_status = "connected" if db else "failed"
        except Exception as db_err:
            db_status = f"error: {str(db_err)}"

        staff_count = 0
        try:
            from backend.database_firestore import FirestoreDB
            staff = FirestoreDB.get_staff()
            staff_count = len(staff)
        except:
            pass

        return {
            "status": "ok",
            "version": "1.3.1",
            "db": db_status,
            "staff_count": staff_count,
            "db_error": os.getenv("FIREBASE_INIT_ERROR", "none"),
            "environment": "vercel" if os.getenv("VERCEL") else "local"
        }
except:
    pass

# Vercel needs the 'app' object
app = app
