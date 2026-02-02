from http.server import BaseHTTPRequestHandler
import json
import os

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({
            "status": "raw_v202",
            "cwd": os.getcwd(),
            "env": os.environ.get("VERCEL_ENV", "local")
        }).encode())
        return
