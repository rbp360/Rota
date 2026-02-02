from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import sys
import os
import traceback

app = FastAPI()

# 1. LOCAL HEALTH CHECK
@app.get("/api/health")
async def health_check():
    return {
        "status": "nested_mode",
        "version": "1.8.5",
        "info": "Checking for backend folder...",
        "backend_exists": os.path.exists(os.path.join(os.path.dirname(__file__), "backend")),
        "sys_path": sys.path
    }

# 2. NESTED IMPORT
@app.post("/api/import-staff")
async def handle_import(request: Request):
    try:
        # Note: In Vercel, if we put 'backend' inside 'api', it's available as a local import
        from .backend.main_firestore import import_staff_bridge
        return await import_staff_bridge(request)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "trace": traceback.format_exc()}
        )

# Standard app exposure
app = app
