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

@app.get("/health")
async def health():
    return {
        "status": "online",
        "version": "4.0.1",
        "msg": "I AM RESPONDING WITHOUT THE API PREFIX."
    }

@app.post("/import-staff")
async def importer(request: Request):
    return {"msg": "Importer reached"}

@app.all("/{path:path}")
async def catch_all(path: str):
    return {"path": path, "msg": "Catch-all reached"}
