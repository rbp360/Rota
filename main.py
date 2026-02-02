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
def read_root():
    return {"status": "online", "message": "Render is responding!", "version": "4.0.4"}

@app.get("/health")
def read_health():
    return {"status": "ok", "msg": "Sync tests beginning"}

@app.post("/import-staff")
def importer():
    return {"msg": "Importer hit"}

@app.get("/{path:path}")
def catch_all(path: str):
    return {"path": path, "msg": "Catch-all reached 4.0.4"}
