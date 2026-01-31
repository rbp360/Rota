import os
import sys
import traceback
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Create the app instance immediately so Vercel sees it
app = FastAPI()

# Add the project root to path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.append(root_dir)

# STANDALONE HEALTH CHECK (No dependencies)
@app.get("/api/health")
async def health():
    return {
        "status": "ready",
        "env": "vercel" if os.getenv("VERCEL") else "local",
        "python": sys.version,
        "root": root_dir
    }

# LAZY BACKEND LOADING
# This captures every other request and only THEN tries to load the backend
@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_to_backend(request: Request, path: str):
    try:
        # We import inside the handler so the worker starts up first!
        from backend.main_firestore import app as backend_app
        
        # Manually route the request to the backend_app
        # This is a simple 'middleware' approach
        scope = request.scope
        # Update the path to what the backend expects (without the prefix if needed)
        # However, backend_app likely has routes defined as /api/...
        
        # Use the backend_app to handle the request
        async def receive():
            return await request.receive()
            
        async def send(message):
            # This is a bit complex for a proxy, so let's try a simpler approach first:
            # Just import and replace the handler if we can, but since FastAPI is already running
            # We will just call the backend logic directly or report the error.
            pass

        # For diagnostic purposes, if we get here, the backend LOADED.
        # Let's just return a success message for now to confirm loading works.
        return {"status": "backend_loaded", "target_path": path}

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": "Lazy Backend Loading Failed",
                "message": str(e),
                "trace": traceback.format_exc(),
                "cwd": os.getcwd(),
                "files": os.listdir(root_dir) if os.path.exists(root_dir) else "unknown"
            }
        )

# Ensure 'app' is at the top level for Vercel
app = app
