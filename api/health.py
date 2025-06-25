"""
Health check endpoint for Vercel deployment.
"""

import json
from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Health check endpoint."""
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()

        response = {"status": "healthy", "service": "dicebot-slack-vercel"}

        self.wfile.write(json.dumps(response).encode())
        return
