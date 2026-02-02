try:
    from fastapi import FastAPI
    app = FastAPI()

    @app.get("/api/health")
    async def health():
        return {"status": "ok_v199"}

    @app.all("/api/{path:path}")
    async def catch(path):
        return {"path": path}
except Exception as e:
    # If FastAPI fails to load, use a Raw Handler fallback
    from http.server import BaseHTTPRequestHandler
    import json
    class handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
    app = None
