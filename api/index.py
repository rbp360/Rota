from fastapi import FastAPI

app = FastAPI()

@app.get("/api/health")
def health():
    return {"status": "ok", "ver": "1.6.6"}

@app.get("/api/index")
def index():
    return {"status": "ok", "ver": "1.6.6"}
