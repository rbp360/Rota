from fastapi import FastAPI

app = FastAPI()

@app.get("/api/health")
async def health():
    return {"status": "v2.3.1-zero_config"}

@app.get("/api")
async def root():
    return {"status": "alive", "version": "2.3.1"}

app = app
