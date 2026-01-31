import sys
import os
import traceback
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Add the root directory to sys.path so we can find the 'backend' folder
# When running on Vercel, the current file is in /api/index.py
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.append(root_dir)

try:
    from backend.main_firestore import app
except Exception as e:
    # If the backend fails to load, create a reporter app
    app = FastAPI()
    error_detail = str(e)
    error_stack = traceback.format_exc()

    @app.get("/api/{path:path}")
    async def report_crash(path: str):
        return JSONResponse(
            status_code=500,
            content={
                "error": "Initialization Failed",
                "message": error_detail,
                "stack": error_stack,
                "current_dir": os.getcwd(),
                "sys_path": sys.path
            }
        )

# Identity for Vercel
app = app
