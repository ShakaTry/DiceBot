import json
from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        response_data = {"message": "Working endpoint!", "status": "ok", "vercel": True}
        self.wfile.write(json.dumps(response_data).encode())
