from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import sys
import os

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root not in sys.path:
    sys.path.insert(0, root)

app = FastAPI()

@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"DEBUG: Path: {request.url.path}")
    return await call_next(request)

try:
    from backend.main_firestore import app as backend_app
    app = backend_app
except Exception as e:
    @app.get("/api/health")
    def fail(request: Request):
        return {"status": "crash", "error": str(e), "path": request.url.path}

# Mandatory
app = app
