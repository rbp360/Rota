from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/api/health")
async def health():
    return {"status": "minimal_start_working"}

@app.get("/api/{path:path}")
async def catch_all(path: str):
    return {"message": "Minimal API is alive", "path": path}

app = app
