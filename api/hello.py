import json
from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()

        response = {
            "message": "Hello from Vercel Python!",
            "status": "working",
            "timestamp": "2025-06-25",
        }

        self.wfile.write(json.dumps(response).encode())
        return
