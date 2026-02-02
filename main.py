from fastapi import FastAPI
import os

app = FastAPI()

@app.get("/")
def root():
    return {
        "status": "online",
        "version": "4.5.0-LEAN",
        "msg": "I AM CLEAN AND REBUILT"
    }

@app.get("/api/health")
def health():
    return {"status": "ok", "version": "4.5.0-LEAN"}
