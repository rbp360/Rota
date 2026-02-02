from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import sys
import os

app = FastAPI()

@app.get("/api/health")
async def health():
    return {
        "status": "online",
        "version": "2.2.4",
        "msg": "Libraries loaded, standing by for database signal."
    }

@app.post("/api/import-staff")
async def handle_import(request: Request):
    try:
        data = await request.json()
        from backend.main_firestore import import_staff_bridge
        return await import_staff_bridge(request)
    except Exception as e:
        import traceback
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "trace": traceback.format_exc()}
        )

app = app
