from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import os

app = FastAPI()

@app.get("/api/health")
async def health():
    return {
        "status": "baseline_v2",
        "version": "1.5.4",
        "env": os.environ.get("VERCEL_ENV", "unknown")
    }

@app.all("/api/import-staff")
async def import_staff(request: Request):
    return {"message": "Endpoint reached. Ready for data push."}

# The variable name MUST be 'app' for Vercel's auto-detection of FastAPI
app = app
