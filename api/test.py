"""
Test endpoint for Vercel deployment.
"""

import json
from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Test endpoint."""
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()

        response = {"status": "working", "message": "Vercel deployment successful"}

        self.wfile.write(json.dumps(response).encode())
        return
