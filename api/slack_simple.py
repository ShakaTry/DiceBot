"""
Simplified Slack commands endpoint that works without DiceBot imports.
"""

import json
import urllib.parse
from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Handle Slack slash commands."""
        try:
            # Parse form data
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length).decode("utf-8")
            form_data = urllib.parse.parse_qs(post_data)

            # Extract command info
            command = form_data.get("command", [""])[0]
            text = form_data.get("text", [""])[0]
            user_name = form_data.get("user_name", [""])[0]

            # Handle commands
            if command == "/issue":
                response_text = (
                    f"🐙 GitHub Issue Command Received!\n"
                    f"Text: {text}\nUser: {user_name}\n\n"
                    f"✅ Integration working!"
                )
            elif command == "/dicebot-status":
                response_text = "🤖 DiceBot Status: ✅ Online and ready!"
            else:
                response_text = f"❓ Unknown command: {command}"

            response = {"response_type": "in_channel", "text": response_text}

            # Send response
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())

        except Exception as e:
            # Error response
            error_response = {"response_type": "ephemeral", "text": f"❌ Error: {str(e)}"}

            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(error_response).encode())
