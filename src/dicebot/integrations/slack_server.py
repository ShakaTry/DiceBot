"""
Flask server for Slack bot integration.
"""

import logging
import os
from typing import Any

from flask import Flask, jsonify, request
from slack_sdk.signature import SignatureVerifier

from .slack_bot import SlackBot


class SlackServer:
    """Flask server for handling Slack bot requests."""

    def __init__(self, bot_token: str, signing_secret: str, port: int = 3000):
        """Initialize Slack server.

        Args:
            bot_token: Slack bot token
            signing_secret: Slack signing secret
            port: Server port
        """
        self.app = Flask(__name__)
        self.bot = SlackBot(bot_token, signing_secret)
        self.signature_verifier = SignatureVerifier(signing_secret)
        self.port = port
        self.logger = logging.getLogger(__name__)

        # Setup routes
        self._setup_routes()

    def _setup_routes(self) -> None:
        """Setup Flask routes."""

        @self.app.route("/slack/events", methods=["POST"])
        def slack_events():
            """Handle Slack events."""
            try:
                # Verify request signature
                if not self._verify_request():
                    return jsonify({"error": "Invalid signature"}), 401

                data = request.get_json()

                # Handle URL verification
                if data.get("type") == "url_verification":
                    return jsonify({"challenge": data["challenge"]})

                # Handle events
                if data.get("type") == "event_callback":
                    event = data.get("event", {})
                    self._handle_event(event)

                return jsonify({"status": "ok"})

            except Exception as e:
                self.logger.error(f"Events endpoint error: {e}")
                return jsonify({"error": "Internal server error"}), 500

        @self.app.route("/slack/commands", methods=["POST"])
        def slack_commands():
            """Handle Slack slash commands."""
            try:
                # Verify request signature
                if not self._verify_request():
                    return jsonify({"error": "Invalid signature"}), 401

                # Parse command
                command = request.form.get("command")
                text = request.form.get("text", "")
                channel_id = request.form.get("channel_id")
                user_id = request.form.get("user_id")

                # Handle command
                self._handle_command(command, text, channel_id, user_id)

                return jsonify({"response_type": "in_channel", "text": "Command received!"})

            except Exception as e:
                self.logger.error(f"Commands endpoint error: {e}")
                return jsonify({"error": "Internal server error"}), 500

        @self.app.route("/slack/interactive", methods=["POST"])
        def slack_interactive():
            """Handle Slack interactive components."""
            try:
                # Verify request signature
                if not self._verify_request():
                    return jsonify({"error": "Invalid signature"}), 401

                # Handle interactive components (buttons, modals, etc.)
                payload = request.form.get("payload")
                if payload:
                    import json

                    data = json.loads(payload)
                    self._handle_interactive(data)

                return jsonify({"status": "ok"})

            except Exception as e:
                self.logger.error(f"Interactive endpoint error: {e}")
                return jsonify({"error": "Internal server error"}), 500

        @self.app.route("/health", methods=["GET"])
        def health_check():
            """Health check endpoint."""
            return jsonify(
                {
                    "status": "healthy",
                    "service": "dicebot-slack-server",
                    "version": "1.0.0",
                }
            )

    def _verify_request(self) -> bool:
        """Verify Slack request signature."""
        try:
            timestamp = request.headers.get("X-Slack-Request-Timestamp")
            signature = request.headers.get("X-Slack-Signature")
            body = request.get_data(as_text=True)

            return self.signature_verifier.is_valid(body, timestamp, signature)

        except Exception as e:
            self.logger.error(f"Signature verification failed: {e}")
            return False

    def _handle_event(self, event: dict[str, Any]) -> None:
        """Handle Slack event."""
        event_type = event.get("type")

        if event_type == "message":
            # Handle direct messages or mentions
            channel = event.get("channel")
            user = event.get("user")
            text = event.get("text", "")

            # Simple command parsing from message
            if "status" in text.lower():
                self.bot.handle_status(channel, user)
            elif "results" in text.lower():
                self.bot.handle_results(channel, user)

    def _handle_command(self, command: str, text: str, channel: str, user: str) -> None:
        """Handle slash command."""
        if command in self.bot.commands:
            handler = self.bot.commands[command]
            if command == "/dicebot-simulate":
                handler(channel, user, text)
            else:
                handler(channel, user)
        else:
            self.bot.send_message(channel, f"Unknown command: {command}")

    def _handle_interactive(self, data: dict[str, Any]) -> None:
        """Handle interactive component."""
        # Handle button clicks, modal submissions, etc.
        action_type = data.get("type")

        if action_type == "block_actions":
            # Handle button clicks
            actions = data.get("actions", [])
            channel = data.get("channel", {}).get("id")
            user = data.get("user", {}).get("id")

            for action in actions:
                action_id = action.get("action_id")

                if action_id == "start_simulation":
                    self.bot.handle_simulate(channel, user, "")
                elif action_id == "stop_simulation":
                    self.bot.handle_stop(channel, user)

    def run(self, debug: bool = False, host: str = "0.0.0.0") -> None:
        """Run the Flask server.

        Args:
            debug: Enable debug mode
            host: Host address
        """
        self.logger.info(f"Starting Slack server on {host}:{self.port}")
        self.app.run(host=host, port=self.port, debug=debug)


def create_slack_server() -> SlackServer:
    """Create Slack server from environment variables."""
    bot_token = os.getenv("SLACK_BOT_TOKEN")
    signing_secret = os.getenv("SLACK_SIGNING_SECRET")
    port = int(os.getenv("SLACK_SERVER_PORT", "3000"))

    if not bot_token or not signing_secret:
        raise ValueError("SLACK_BOT_TOKEN and SLACK_SIGNING_SECRET must be set")

    return SlackServer(bot_token, signing_secret, port)


if __name__ == "__main__":
    # Development server
    server = create_slack_server()
    server.run(debug=True)
