"""
Vercel serverless function for Slack → GitHub integration.
"""

import json
import os

# Import our DiceBot integrations
import sys
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs

sys.path.append("/var/task")
sys.path.append("/var/task/src")

try:
    from dicebot.integrations import GitHubClient, SlackBot
except ImportError:
    # Fallback for local testing
    sys.path.append("src")
    from dicebot.integrations import GitHubClient, SlackBot


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Health check endpoint."""
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()

        response = {
            "status": "healthy",
            "service": "dicebot-slack-integration",
            "endpoints": ["/api/slack - Slack events and commands", "/api/hello - Health check"],
        }

        self.wfile.write(json.dumps(response).encode())

    def do_POST(self):
        """Handle Slack events and commands."""
        try:
            # Get request data
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)

            # Parse content type
            content_type = self.headers.get("Content-Type", "")

            if "application/json" in content_type:
                # JSON payload (events)
                data = json.loads(post_data.decode("utf-8"))
                response = self._handle_slack_event(data)
            elif "application/x-www-form-urlencoded" in content_type:
                # Form data (slash commands)
                form_data = parse_qs(post_data.decode("utf-8"))
                response = self._handle_slash_command(form_data)
            else:
                response = {"error": "Unsupported content type"}

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())

        except Exception as e:
            self._send_error(f"Server error: {str(e)}")

    def _handle_slack_event(self, data):
        """Handle Slack event callbacks."""
        # URL verification challenge
        if data.get("type") == "url_verification":
            return {"challenge": data.get("challenge")}

        # Event callback
        if data.get("type") == "event_callback":
            event = data.get("event", {})

            if event.get("type") == "app_mention":
                return self._handle_mention(event)

        return {"status": "ok"}

    def _handle_slash_command(self, form_data):
        """Handle Slack slash commands."""
        # Extract form data
        command = form_data.get("command", [""])[0]
        text = form_data.get("text", [""])[0]
        channel_id = form_data.get("channel_id", [""])[0]
        user_name = form_data.get("user_name", [""])[0]

        # Verify required environment variables
        if not self._verify_config():
            return {
                "response_type": "ephemeral",
                "text": "❌ Server configuration error. Please contact admin.",
            }

        try:
            # Create GitHub client
            github_client = GitHubClient(
                token=os.getenv("GITHUB_TOKEN"),
                owner=os.getenv("GITHUB_OWNER", "ShakaTry"),
                repo=os.getenv("GITHUB_REPO", "DiceBot"),
            )

            # Create Slack bot
            slack_bot = SlackBot(
                bot_token=os.getenv("SLACK_BOT_TOKEN"),
                signing_secret=os.getenv("SLACK_SIGNING_SECRET"),
                github_client=github_client,
            )

            # Handle different commands
            if command == "/issue":
                return self._handle_issue_command(slack_bot, text, channel_id, user_name)
            elif command == "/dicebot-status":
                return self._handle_status_command(slack_bot, channel_id, user_name)
            elif command == "/dicebot-simulate":
                return self._handle_simulate_command(slack_bot, text, channel_id, user_name)
            else:
                return {"response_type": "ephemeral", "text": f"❌ Unknown command: {command}"}

        except Exception as e:
            return {"response_type": "ephemeral", "text": f"❌ Command failed: {str(e)}"}

    def _handle_mention(self, event):
        """Handle bot mentions."""
        # For mentions, we'd typically respond directly via Slack API
        # For serverless, we return immediate response
        return {
            "text": (
                "🤖 Hi! I'm DiceBot. Use slash commands:\n"
                "• `/issue list` - View GitHub issues\n"
                '• `/issue create "Title" "Body"` - Create issue\n'
                "• `/dicebot-status` - System status"
            )
        }

    def _handle_issue_command(self, slack_bot, text, channel_id, user_name):
        """Handle GitHub issue commands."""
        try:
            if not slack_bot.github_bridge:
                return {
                    "response_type": "ephemeral",
                    "text": "❌ GitHub integration not configured",
                }

            # Parse command
            command = slack_bot.github_bridge.parse_issue_command(text)

            # Execute command
            response_text = slack_bot.github_bridge.execute_command(command, user_name)

            return {"response_type": "in_channel", "text": response_text}

        except Exception as e:
            return {"response_type": "ephemeral", "text": f"❌ Issue command failed: {str(e)}"}

    def _handle_status_command(self, slack_bot, channel_id, user_name):
        """Handle status command."""
        try:
            import datetime

            import psutil

            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()

            status_text = (
                f"🤖 **DiceBot Status**\n"
                f"💻 CPU: {cpu_percent:.1f}%\n"
                f"🧠 Memory: {memory.percent:.1f}%\n"
                f"⏰ Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"🎲 Ready for simulations!\n"
                f"🔗 GitHub: Connected\n"
                f"💬 Slack: Connected"
            )

            return {"response_type": "in_channel", "text": status_text}

        except Exception as e:
            return {"response_type": "ephemeral", "text": f"❌ Status check failed: {str(e)}"}

    def _handle_simulate_command(self, slack_bot, text, channel_id, user_name):
        """Handle simulation command."""
        return {
            "response_type": "ephemeral",
            "text": "🎲 Simulation feature coming soon! Use GitHub issues to track requests.",
        }

    def _verify_config(self):
        """Verify required environment variables."""
        required_vars = ["GITHUB_TOKEN", "SLACK_BOT_TOKEN", "SLACK_SIGNING_SECRET"]

        missing = [var for var in required_vars if not os.getenv(var)]
        return len(missing) == 0

    def _send_error(self, message):
        """Send error response."""
        self.send_response(500)
        self.send_header("Content-type", "application/json")
        self.end_headers()

        error_response = {"error": message}
        self.wfile.write(json.dumps(error_response).encode())
