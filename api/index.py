from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import sys
import os

# Root path for backend folder
root_dir = "/var/task"
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

app = FastAPI()

@app.get("/api/health")
async def health():
    return {
        "status": "online",
        "version": "2.1.3",
        "msg": "Speedy Startup Initialized"
    }

@app.post("/api/import-staff")
async def handle_import(request: Request):
    try:
        from backend.main_firestore import import_staff_bridge
        return await import_staff_bridge(request)
    except Exception as e:
        import traceback
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "trace": traceback.format_exc()}
        )

# EXPORT
app = app
