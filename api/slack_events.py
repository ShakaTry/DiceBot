"""
Slack events endpoint for Vercel serverless deployment.
"""

import json
import os
import sys
from http.server import BaseHTTPRequestHandler

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Handle Slack events."""
        try:
            # Parse JSON data
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length).decode("utf-8")
            event_data = json.loads(post_data)

            # Handle URL verification challenge
            if event_data.get("type") == "url_verification":
                challenge = event_data.get("challenge", "")

                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()

                response = {"challenge": challenge}
                self.wfile.write(json.dumps(response).encode())
                return

            # Handle actual events
            if event_data.get("type") == "event_callback":
                self._handle_event_callback(event_data)

            # Send OK response
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()

            response = {"status": "ok"}
            self.wfile.write(json.dumps(response).encode())

        except Exception as e:
            # Error response
            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.end_headers()

            error_response = {"error": f"Event handling failed: {str(e)}"}
            self.wfile.write(json.dumps(error_response).encode())

    def _handle_event_callback(self, event_data: dict) -> None:
        """Handle Slack event callback."""
        event = event_data.get("event", {})
        event_type = event.get("type")

        if event_type == "app_mention":
            # Bot was mentioned
            self._handle_mention(event)
        elif event_type == "message" and event.get("channel_type") == "im":
            # Direct message to bot
            self._handle_direct_message(event)

    def _handle_mention(self, event: dict) -> None:
        """Handle bot mention."""
        # Log the mention (in production, you'd respond via Slack API)
        channel = event.get("channel")
        user = event.get("user")
        text = event.get("text", "")

        print(f"Bot mentioned in {channel} by {user}: {text}")
        # TODO: Implement response via Slack Web API

    def _handle_direct_message(self, event: dict) -> None:
        """Handle direct message."""
        # Log the DM (in production, you'd respond via Slack API)
        user = event.get("user")
        text = event.get("text", "")

        print(f"Direct message from {user}: {text}")
        # TODO: Implement response via Slack Web API
