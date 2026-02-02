from fastapi import FastAPI

app = FastAPI()

@app.get("/api/health")
async def health():
    return {"status": "baseline_test", "version": "1.9.2"}

@app.all("/api/{path:path}")
async def catch_all(path: str):
    return {"message": f"Path {path} works in baseline mode."}

app = app
