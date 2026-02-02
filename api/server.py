from fastapi import FastAPI

app = FastAPI()

@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "2.2.5"}

@app.all("/api/{path:path}")
async def catch_all(path: str):
    return {"path": path}

app = app
