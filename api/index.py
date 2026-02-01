from fastapi import FastAPI

app = FastAPI()

@app.get("/api/health")
def health():
    return {"status": "ok_lite", "ver": "1.7.3"}

@app.all("/api/import-staff")
def imp():
    return {"status": "ready"}
