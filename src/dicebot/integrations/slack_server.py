"""
Flask server for handling Slack events and slash commands.
"""

import json
import logging
from collections.abc import Callable
from typing import Any

from flask import Flask, Response, jsonify, request

from .slack_bot import SlackBot


class SlackServer:
    """Flask server for Slack integration."""

    def __init__(self, slack_bot: SlackBot, debug: bool = False):
        """Initialize Slack server.

        Args:
            slack_bot: Configured SlackBot instance
            debug: Enable Flask debug mode
        """
        self.slack_bot = slack_bot
        self.app = Flask(__name__)
        self.app.debug = debug
        self.logger = logging.getLogger(__name__)

        # Register routes
        self._register_routes()

    def _register_routes(self) -> None:
        """Register Flask routes."""

        @self.app.route("/health", methods=["GET"])
        def health_check() -> Response:  # type: ignore[misc]
            """Health check endpoint."""
            return jsonify({"status": "healthy", "service": "dicebot-slack"})

        @self.app.route("/slack/events", methods=["POST"])
        def handle_slack_events() -> Response | tuple[Response, int]:  # type: ignore[misc]
            """Handle Slack events (messages, mentions, etc.)."""
            try:
                # Verify request
                if not self._verify_slack_request():
                    return jsonify({"error": "Invalid request"}), 401

                # Parse event data
                event_data: dict[str, Any] = request.get_json() or {}

                # Handle URL verification challenge
                if event_data.get("type") == "url_verification":
                    return jsonify({"challenge": event_data.get("challenge")})

                # Handle actual events
                if event_data.get("type") == "event_callback":
                    self._handle_event_callback(event_data)

                return jsonify({"status": "ok"})

            except Exception as e:
                self.logger.error(f"Event handling failed: {e}")
                return jsonify({"error": "Internal server error"}), 500

        @self.app.route("/slack/commands", methods=["POST"])
        def handle_slack_commands() -> Response | tuple[Response, int]:  # type: ignore[misc]
            """Handle Slack slash commands."""
            try:
                # Verify request
                if not self._verify_slack_request():
                    return jsonify({"error": "Invalid request"}), 401

                # Parse command data
                command_data: dict[str, str] = request.form.to_dict()

                # Extract command info
                command = command_data.get("command", "")
                text = command_data.get("text", "")
                channel_id = command_data.get("channel_id", "")
                user_name = command_data.get("user_name", "")

                # Handle command
                response = self._handle_slash_command(command, text, channel_id, user_name)

                return jsonify(response)

            except Exception as e:
                self.logger.error(f"Command handling failed: {e}")
                return jsonify({"response_type": "ephemeral", "text": f"❌ Command failed: {e}"})

        @self.app.route("/slack/interactive", methods=["POST"])
        def handle_slack_interactive() -> Response | tuple[Response, int]:  # type: ignore[misc]
            """Handle Slack interactive components (buttons, modals, etc.)."""
            try:
                # Verify request
                if not self._verify_slack_request():
                    return jsonify({"error": "Invalid request"}), 401

                # Parse payload
                payload: dict[str, Any] = json.loads(request.form.get("payload", "{}"))

                # Handle interactive component
                response = self._handle_interactive_component(payload)

                return jsonify(response)

            except Exception as e:
                self.logger.error(f"Interactive handling failed: {e}")
                return jsonify({"text": f"❌ Interaction failed: {e}"})

    def _verify_slack_request(self) -> bool:
        """Verify Slack request signature."""
        try:
            headers: dict[str, Any] = dict(request.headers)
            body: str = request.get_data(as_text=True)

            return self.slack_bot.verify_request(headers, body)

        except Exception as e:
            self.logger.error(f"Request verification failed: {e}")
            return False

    def _handle_event_callback(self, event_data: dict[str, Any]) -> None:
        """Handle Slack event callback."""
        event: dict[str, Any] = event_data.get("event", {})
        event_type: str | None = event.get("type")

        if event_type == "app_mention":
            # Bot was mentioned
            self._handle_mention(event)
        elif event_type == "message":
            # Message in channel (if bot is in channel)
            self._handle_message(event)

    def _handle_mention(self, event: dict[str, Any]) -> None:
        """Handle bot mention."""
        channel: str | None = event.get("channel")
        user: str | None = event.get("user")
        text: str = event.get("text", "")

        # Remove bot mention from text
        text = self._clean_mention_text(text)

        # Send status if just mentioned without command
        if not text.strip():
            if channel and user:
                self.slack_bot.handle_status(channel, user)
        else:
            # Try to parse as a command
            if text.startswith("status") and channel and user:
                self.slack_bot.handle_status(channel, user)
            elif text.startswith("simulate") and channel and user:
                self.slack_bot.handle_simulate(channel, user, text[8:].strip())
            elif text.startswith("results") and channel and user:
                self.slack_bot.handle_results(channel, user)
            elif text.startswith("issue") and channel and user:
                self.slack_bot.handle_github_issue(channel, user, text[5:].strip())
            elif channel:
                self.slack_bot.send_message(
                    channel,
                    "🤖 Hi! I'm DiceBot. Try:\n• `@dicebot status`\n• `@dicebot simulate --strategy fibonacci`\n• `@dicebot issue list`",
                )

    def _handle_message(self, event: dict[str, Any]) -> None:
        """Handle regular message (if needed)."""
        # For now, only respond to mentions
        # Could be extended for channel monitoring
        pass

    def _clean_mention_text(self, text: str) -> str:
        """Remove bot mention from text."""
        # Remove <@BOTID> format mentions
        import re

        cleaned = re.sub(r"<@[UW][A-Z0-9]+>", "", text).strip()
        return cleaned

    def _handle_slash_command(
        self, command: str, text: str, channel: str, user: str
    ) -> dict[str, Any]:
        """Handle slash command and return response."""

        # Map slash commands to bot methods
        command_handlers: dict[str, Callable[[], dict[str, Any]]] = {
            "/dicebot-status": lambda: self._execute_and_respond(
                self.slack_bot.handle_status, channel, user
            ),
            "/dicebot-simulate": lambda: self._execute_and_respond(
                self.slack_bot.handle_simulate, channel, user, text
            ),
            "/dicebot-stop": lambda: self._execute_and_respond(
                self.slack_bot.handle_stop, channel, user
            ),
            "/dicebot-results": lambda: self._execute_and_respond(
                self.slack_bot.handle_results, channel, user
            ),
            "/issue": lambda: self._execute_and_respond(
                self.slack_bot.handle_github_issue, channel, user, text
            ),
        }

        handler: Callable[[], dict[str, Any]] | None = command_handlers.get(command)

        if handler:
            return handler()
        else:
            return {"response_type": "ephemeral", "text": f"❌ Unknown command: {command}"}

    def _execute_and_respond(self, handler_func: Callable[..., None], *args: Any) -> dict[str, Any]:
        """Execute handler and return appropriate response."""
        try:
            # Execute the handler (it sends message directly to Slack)
            handler_func(*args)

            # Return immediate response for slash command
            return {
                "response_type": "ephemeral",
                "text": "🎲 Command executed! Check the channel for results.",
            }

        except Exception as e:
            self.logger.error(f"Handler execution failed: {e}")
            return {"response_type": "ephemeral", "text": f"❌ Command failed: {e}"}

    def _handle_interactive_component(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Handle interactive components (buttons, etc.)."""
        component_type: str | None = payload.get("type")

        if component_type == "block_actions":
            # Handle button clicks
            actions: list[dict[str, Any]] = payload.get("actions", [])
            for action in actions:
                action_id: str | None = action.get("action_id")

                if action_id == "simulate_quick":
                    # Quick simulate button
                    channel: str | None = payload.get("channel", {}).get("id")
                    user: str | None = payload.get("user", {}).get("name")

                    if channel and user:
                        self.slack_bot.handle_simulate(
                            channel, user, "--strategy fibonacci --preset conservative"
                        )

                    return {"text": "🎲 Quick simulation started!"}

        return {"text": "👍 Action received"}

    def run(self, host: str = "0.0.0.0", port: int = 3000) -> None:
        """Run the Flask server.

        Args:
            host: Host to bind to
            port: Port to listen on
        """
        self.logger.info(f"Starting Slack server on {host}:{port}")
        self.app.run(host=host, port=port, debug=self.app.debug)

    @classmethod
    def create_from_env(cls, debug: bool = False) -> "SlackServer":
        """Create SlackServer from environment variables.

        Args:
            debug: Enable Flask debug mode

        Returns:
            Configured SlackServer instance
        """
        slack_bot = SlackBot.create_from_env()
        return cls(slack_bot, debug)


def create_app() -> Flask:
    """Factory function to create Flask app for deployment."""
    server = SlackServer.create_from_env()
    return server.app


if __name__ == "__main__":
    # Run server directly
    import argparse

    parser = argparse.ArgumentParser(description="Run DiceBot Slack server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=3000, help="Port to listen on")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    try:
        server = SlackServer.create_from_env(debug=args.debug)
        server.run(host=args.host, port=args.port)
    except Exception as e:
        print(f"Failed to start server: {e}")
        exit(1)
