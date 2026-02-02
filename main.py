from fastapi import FastAPI
import os

app = FastAPI()

@app.get("/")
def root():
    return {
        "status": "online",
        "version": "4.7.0-DEBUG",
        "msg": "Force version bump"
    }

@app.get("/api/health")
def health():
    return {"status": "ok", "version": "4.7.0-DEBUG"}
