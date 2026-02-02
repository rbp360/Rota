import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
import traceback

# Add the current directory to sys.path so we can import 'backend'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = FastAPI(title="RotaAI Render API")

# Performance Settings: CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": "online", "message": "RotaAI is running on Render!"}

@app.get("/api/health")
async def health():
    info = {
        "status": "online",
        "version": "3.0.0",
        "platform": "Render",
        "db": "checking..."
    }
    try:
        from backend.database_firestore import get_db, FirestoreDB
        db = get_db()
        if db:
            info["db"] = "connected"
            info["staff_count"] = len(FirestoreDB.get_staff())
        else:
            info["db"] = "failed_init"
    except Exception as e:
        info["db"] = f"error: {str(e)}"
    
    return info

@app.post("/api/import-staff")
async def handle_import(request: Request):
    try:
        from backend.main_firestore import import_staff_bridge
        return await import_staff_bridge(request)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "trace": traceback.format_exc()}
        )

# Proxy other /api routes if needed, or simply let frontend call them.
# The backend/main_firestore.py already has its own FastAPI app ('app')
# But for simplicity, we provide the main bridges here.

if __name__ == "__main__":
    # Render provides a 'PORT' environment variable
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
