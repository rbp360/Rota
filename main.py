from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(title="RotaAI Render Status")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": "online", "message": "Render is responding!"}

@app.get("/api/health")
async def health():
    return {
        "status": "online",
        "version": "4.0.0",
        "msg": "I AM RESPONDING. If you see this, the 502 issue is resolved."
    }

@app.all("/api/{path:path}")
async def catch_all(path: str):
    return {"path": path, "msg": "API is live but logic is temporarily hidden for debugging."}
