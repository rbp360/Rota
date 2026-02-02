from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import os
import traceback

app = FastAPI()

@app.get("/api/health")
async def health():
    return {"status": "v2.2.2-dry_run", "msg": "Standing by for POST test."}

@app.post("/api/import-staff")
async def dry_run_import(request: Request):
    try:
        data = await request.json()
        count = len(data)
        return {
            "status": "dry_run_success",
            "received_count": count,
            "msg": "If you see this, the connection and JSON parsing are WORKING. The error is in the Firestore/Backend initialization."
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "trace": traceback.format_exc()}
        )

app = app
