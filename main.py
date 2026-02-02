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
    return {"status": "online", "message": "Render is responding!", "version": "4.0.3"}

@app.get("/api/health")
def read_health():
    return {"status": "ok", "msg": "API Path Restored"}

@app.post("/api/import-staff")
def importer():
    return {"msg": "API Importer hit"}

@app.all("/{path:path}")
def catch_all(path: str):
    return {"path": path, "msg": "Root Catch-all reached", "hint": "Try prefixing with /api"}
