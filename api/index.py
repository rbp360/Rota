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
    
    @app.get("/api/{path:path}")
    async def report_error(path: str):
        return JSONResponse(
            status_code=500,
            content={
                "error": "Backend Initialization Failed",
                "detail": error_msg,
                "trace": stack_trace,
                "current_dir": os.getcwd(),
                "sys_path": sys.path
            }
        )

# Add a health check at the very top level
@app.get("/api/health")
async def health():
    return {"status": "ok", "environment": "vercel" if os.getenv("VERCEL") else "local"}

# Vercel needs the 'app' object
app = app
