"""
Slack commands endpoint for Vercel serverless deployment.
"""

import json
import os
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

try:
    from dicebot.integrations import GitHubClient, SlackGitHubBridge
except ImportError as e:
    print(f"Import error: {e}")
    # Fallback for serverless environment
    pass


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
            channel_id = form_data.get("channel_id", [""])[0]
            user_name = form_data.get("user_name", [""])[0]

            # Process command
            response = self._handle_command(command, text, channel_id, user_name)

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

            error_response = {"response_type": "ephemeral", "text": f"❌ Command failed: {str(e)}"}

            self.wfile.write(json.dumps(error_response).encode())

    def _handle_command(self, command: str, text: str, channel: str, user: str) -> dict:
        """Handle specific slash command."""

        if command == "/issue":
            return self._handle_issue_command(text, user)
        elif command == "/dicebot-status":
            return self._handle_status_command()
        elif command == "/dicebot-simulate":
            return self._handle_simulate_command(text, user)
        else:
            return {"response_type": "ephemeral", "text": f"❌ Unknown command: {command}"}

    def _handle_issue_command(self, text: str, user: str) -> dict:
        """Handle GitHub issue commands."""
        try:
            # Get environment variables
            github_token = os.getenv("GITHUB_TOKEN")
            github_owner = os.getenv("GITHUB_OWNER", "ShakaTry")
            github_repo = os.getenv("GITHUB_REPO", "DiceBot")

            if not github_token:
                return {"response_type": "ephemeral", "text": "❌ GitHub token not configured"}

            # Create GitHub client and bridge
            github_client = GitHubClient(github_token, github_owner, github_repo)
            bridge = SlackGitHubBridge(github_client)

            # Parse and execute command
            command = bridge.parse_issue_command(text)
            response_text = bridge.execute_command(command, user)

            return {"response_type": "in_channel", "text": response_text}

        except Exception as e:
            return {"response_type": "ephemeral", "text": f"❌ Issue command failed: {str(e)}"}

    def _handle_status_command(self) -> dict:
        """Handle status command."""
        status_text = (
            "🤖 **DiceBot Status (Vercel)**\n"
            "✅ Serverless functions active\n"
            "🔗 GitHub integration enabled\n"
            "🎲 Ready for simulations!"
        )
        return {"response_type": "ephemeral", "text": status_text}

    def _handle_simulate_command(self, text: str, user: str) -> dict:
        """Handle simulate command."""
        sim_text = (
            f"🎲 **Simulation Request Received**\n"
            f"Parameters: {text}\n"
            f"User: {user}\n\n"
            f"⚠️ Simulation will be implemented in future versions."
        )
        return {"response_type": "ephemeral", "text": sim_text}
