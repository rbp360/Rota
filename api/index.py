from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import sys
import os
import traceback

# FORCE PATH - Ensure backend is visible
root_dir = "/var/task"
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

app = FastAPI()

@app.get("/api/health")
async def health():
    return {
        "status": "v2.2.1-power_on",
        "msg": "I am awake and waiting for data."
    }

@app.post("/api/import-staff")
async def handle_import(request: Request):
    """
    Surgical Import: Load NOTHING unless this is called.
    """
    print("DEBUG: Import request received")
    try:
        # Load heavy logic only inside the call
        from backend.main_firestore import import_staff_bridge
        return await import_staff_bridge(request)
    except Exception as e:
        err_msg = str(e)
        stack = traceback.format_exc()
        print(f"CRITICAL ERROR: {err_msg}")
        return JSONResponse(
            status_code=500,
            content={"error": err_msg, "trace": stack}
        )

# Standard export for Vercel
app = app
