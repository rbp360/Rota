import os
import sys
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "python": sys.version,
        "cwd": os.getcwd()
    }

@app.get("/api/staff")
async def staff_proxy():
    try:
        from backend.main_firestore import app as backend_app
        return {"status": "backend_found", "message": "Backend logic ready to be restored"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/{path:path}")
async def catch_all(path: str):
    return {"message": "API alive", "path": path}

# This is the important part for Vercel
app = app
