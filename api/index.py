from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/api/health")
async def health():
    return {
        "status": "baseline_test",
        "version": "1.3.7"
    }

@app.get("/api/{path:path}")
async def catch_all(path: str):
    return {"message": f"Path {path} works in baseline mode."}

handler = app
