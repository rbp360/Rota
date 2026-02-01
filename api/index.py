from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import sys
import os

# Ensure backend can be found
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root not in sys.path:
    sys.path.insert(0, root)

try:
    from backend.main_firestore import app as backend_app
    app = backend_app
except Exception as e:
    # Diagnostic fallback
    import traceback
    app = FastAPI()
    _err = str(e)
    _trace = traceback.format_exc()
    @app.get("/api/health")
    def health_diag():
        return {"status": "backend_crash", "error": _err, "trace": _trace}

# Vercel needs 'app'
app = app
