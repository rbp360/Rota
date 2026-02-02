from fastapi import FastAPI

app = FastAPI()

@app.get("/api/health")
async def health():
    return {"status": "ok_v196", "msg": "It is alive!"}

@app.all("/api/import-staff")
async def imp():
    return {"status": "ready"}

app = app
