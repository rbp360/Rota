import os
import sys
import traceback
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Add the project root to the path so we can find the 'backend' folder
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.append(root_dir)

app = None
init_error = None
init_stack = None

try:
    # Attempt to import the actual backend
    from backend.main_firestore import app as backend_app
    app = backend_app
except Exception as e:
    init_error = str(e)
    init_stack = traceback.format_exc()

# If backend failed to load, create a fallback app to report the error
if app is None:
    app = FastAPI()
    
    @app.get("/api/health")
    async def health():
        return {
            "status": "initialization_failed",
            "error": init_error,
            "trace": init_stack,
            "path": sys.path,
            "cwd": os.getcwd()
        }

    @app.get("/api/{path:path}")
    async def catch_all(path: str):
        return JSONResponse(
            status_code=500,
            content={
                "error": "Backend Loading Error",
                "message": init_error,
                "trace": init_stack
            }
        )
else:
    # Backend loaded successfully!
    # Ensure a health check exists
    try:
        @app.get("/api/health")
        async def health():
            return {"status": "ok", "environment": "vercel" if os.getenv("VERCEL") else "local"}
    except:
        # Route might already exist
        pass

# Ensure 'app' is available for Vercel
app = app
