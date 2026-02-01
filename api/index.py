from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        import os
        import sys
        self.wfile.write(bytes('{"status":"extreme_baseline", "python":"' + sys.version + '"}', "utf-8"))
        return
