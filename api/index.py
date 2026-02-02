from fastapi import FastAPI

app = FastAPI()

@app.get("/api/health")
async def health():
    return {"status": "baseline_v193", "msg": "Zero Config Test"}

# For Vercel
app = app
