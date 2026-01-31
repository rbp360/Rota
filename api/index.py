from backend.main_firestore import app

# This allows Vercel to serve the FastAPI app
app = app

@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "Backend is reachable"}
