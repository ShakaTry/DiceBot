"""
Slack interactive components endpoint for Vercel serverless deployment.
"""

import json
import urllib.parse
from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Handle Slack interactive components."""
        try:
            # Parse form data
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length).decode("utf-8")
            form_data = urllib.parse.parse_qs(post_data)

            # Extract payload
            payload_str = form_data.get("payload", ["{}"])[0]
            payload = json.loads(payload_str)

            # Handle interactive component
            response = self._handle_interactive_component(payload)

            # Send response
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()

            self.wfile.write(json.dumps(response).encode())

        except Exception as e:
            # Error response
            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.end_headers()

            error_response = {"text": f"❌ Interaction failed: {str(e)}"}
            self.wfile.write(json.dumps(error_response).encode())

    def _handle_interactive_component(self, payload: dict) -> dict:
        """Handle interactive components (buttons, etc.)."""
        component_type = payload.get("type")

        if component_type == "block_actions":
            # Handle button clicks
            actions = payload.get("actions", [])
            for action in actions:
                action_id = action.get("action_id")

                if action_id == "simulate_quick":
                    return {"text": "🎲 Quick simulation triggered!"}
                elif action_id == "create_issue":
                    return {"text": "📝 Issue creation form opened!"}

        return {"text": "👍 Interactive component received"}
