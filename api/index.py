from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import sys
import os
import traceback

app = FastAPI()

# 1. LOCAL HEALTH CHECK
@app.get("/api/health")
async def health_check():
    vendor_path = "/var/task/_vendor"
    vendor_contents = []
    if os.path.exists(vendor_path):
        vendor_contents = os.listdir(vendor_path)
    
    return {
        "status": "nested_mode",
        "version": "1.8.6",
        "info": "Checking for backend folder...",
        "backend_exists": os.path.exists(os.path.join(os.path.dirname(__file__), "backend")),
        "vendor_path": vendor_path,
        "vendor_contents": vendor_contents[:20],  # show first 20
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
