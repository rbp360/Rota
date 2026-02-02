from fastapi import FastAPI

app = FastAPI()

@app.get("/api/health")
async def health():
    return {"status": "direct_check", "version": "2.0.1"}

# Vercel will map this to /api/health if the folder is 'api'
app = app
