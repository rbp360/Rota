from fastapi import FastAPI, Request
import os
import sys

# Ensure backend can be found
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root not in sys.path:
    sys.path.insert(0, root)

try:
    from backend.main_firestore import app as backend_app
    app = backend_app
except Exception as e:
    # Diagnostic fallback
    app = FastAPI()
    @app.get("/api/health")
    def health_diag():
        import traceback
        return {"status": "crash", "error": str(e), "trace": traceback.format_exc()}

# Vercel's Python runtime auto-detects 'app' for FastAPI
app = app
