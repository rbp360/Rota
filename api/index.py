from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import sys
import os
import traceback

# 1. Path Setup
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root)

# 2. Try to load the real app
try:
    from backend.main_firestore import app
except Exception as e:
    # If the real app crashes, create a diagnostic app
    app = FastAPI()
    _err = str(e)
    _trace = traceback.format_exc()

    @app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
    async def diagnostic_route(request: Request, path: str):
        return JSONResponse(
            status_code=500,
            content={
                "status": "initialization_failed",
                "error": _err,
                "trace": _trace,
                "note": "The backend failed to start. Check your requirements.txt or imports."
            }
        )

# 3. Add Top-Level Health Check (if not already there)
@app.get("/api/health")
async def top_health():
    db_status = "unknown"
    staff_count = 0
    try:
        from backend.database_firestore import get_db, FirestoreDB
        db = get_db()
        db_status = "connected" if db else "failed"
        if db:
            staff = FirestoreDB.get_staff()
            staff_count = len(staff)
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "ok",
        "version": "1.3.6",
        "db": db_status,
        "staff_count": staff_count,
        "environment": "vercel"
    }

# 4. Mandatory export for Vercel
handler = app
