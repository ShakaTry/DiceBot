import json
from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()

        response = {
            "message": "DiceBot Vercel Integration",
            "status": "online",
            "service": "dicebot-slack-github",
            "version": "1.0.0",
            "endpoints": {"health": "/api/", "slack_integration": "/api/slack"},
        }

        self.wfile.write(json.dumps(response).encode())
        return
