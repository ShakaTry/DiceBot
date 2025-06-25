import json
import os
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs

import requests


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Health check endpoint."""
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()

        response = {
            "status": "healthy",
            "service": "dicebot-slack-integration",
            "github_configured": bool(os.getenv("GITHUB_TOKEN")),
            "slack_configured": bool(os.getenv("SLACK_BOT_TOKEN")),
        }

        self.wfile.write(json.dumps(response).encode())

    def do_POST(self):
        """Handle Slack events and commands."""
        try:
            # Get request data
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
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
            return {"status": "ok"}

        return {"status": "ok"}

    def _handle_slash_command(self, form_data):
        """Handle Slack slash commands."""
        command = form_data.get("command", [""])[0]
        text = form_data.get("text", [""])[0]
        user_name = form_data.get("user_name", [""])[0]

        # Check config
        if not self._verify_config():
            return {
                "response_type": "ephemeral",
                "text": "❌ Server configuration error. Missing tokens.",
            }

        if command == "/issue":
            return self._handle_issue_command(text, user_name)
        elif command == "/dicebot-status":
            return self._handle_status_command()
        else:
            return {"response_type": "ephemeral", "text": f"❌ Unknown command: {command}"}

    def _handle_issue_command(self, text, user_name):
        """Handle GitHub issue commands."""
        try:
            parts = text.strip().split()
            if not parts:
                return {
                    "response_type": "ephemeral",
                    "text": "Usage: /issue list|create|show #number",
                }

            action = parts[0].lower()

            if action == "list":
                return self._list_issues()
            elif action == "create" and len(parts) >= 2:
                title = " ".join(parts[1:])
                return self._create_issue(title, user_name)
            elif action == "show" and len(parts) >= 2:
                issue_num = parts[1].lstrip("#")
                return self._show_issue(issue_num)
            else:
                return {
                    "response_type": "ephemeral",
                    "text": "Usage: /issue list | /issue create Title | /issue show #123",
                }

        except Exception as e:
            return {"response_type": "ephemeral", "text": f"❌ Error: {str(e)}"}

    def _list_issues(self):
        """List GitHub issues."""
        try:
            repo_path = (
                f"{os.getenv('GITHUB_OWNER', 'ShakaTry')}/{os.getenv('GITHUB_REPO', 'DiceBot')}"
            )
            url = f"https://api.github.com/repos/{repo_path}/issues"
            headers = {
                "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}",
                "Accept": "application/vnd.github.v3+json",
            }

            response = requests.get(url, headers=headers, params={"state": "open", "per_page": 5})
            response.raise_for_status()

            issues = response.json()

            if not issues:
                return {"response_type": "in_channel", "text": "📂 No open issues found"}

            text = "📋 **Open Issues:**\n"
            for issue in issues[:5]:
                text += f"🟢 **#{issue['number']}**: {issue['title'][:50]}\n"

            return {"response_type": "in_channel", "text": text}

        except Exception as e:
            return {"response_type": "ephemeral", "text": f"❌ Failed to list issues: {str(e)}"}

    def _create_issue(self, title, user_name):
        """Create GitHub issue."""
        try:
            repo_path = (
                f"{os.getenv('GITHUB_OWNER', 'ShakaTry')}/{os.getenv('GITHUB_REPO', 'DiceBot')}"
            )
            url = f"https://api.github.com/repos/{repo_path}/issues"
            headers = {
                "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}",
                "Accept": "application/vnd.github.v3+json",
            }

            body = f"Created from Slack by @{user_name}"
            payload = {"title": title, "body": body}

            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()

            issue = response.json()

            text = (
                f"✅ **Issue Created!**\n🔗 **#{issue['number']}**: {title}\n📎 {issue['html_url']}"
            )
            return {"response_type": "in_channel", "text": text}

        except Exception as e:
            return {"response_type": "ephemeral", "text": f"❌ Failed to create issue: {str(e)}"}

    def _show_issue(self, issue_num):
        """Show GitHub issue details."""
        try:
            repo_path = (
                f"{os.getenv('GITHUB_OWNER', 'ShakaTry')}/{os.getenv('GITHUB_REPO', 'DiceBot')}"
            )
            url = f"https://api.github.com/repos/{repo_path}/issues/{issue_num}"
            headers = {
                "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}",
                "Accept": "application/vnd.github.v3+json",
            }

            response = requests.get(url, headers=headers)
            response.raise_for_status()

            issue = response.json()

            state_emoji = "🟢" if issue["state"] == "open" else "🔴"

            return {
                "response_type": "in_channel",
                "text": (
                    f"{state_emoji} **Issue #{issue['number']}: {issue['title']}**\n"
                    f"📅 **Created**: {issue['created_at'][:10]}\n"
                    f"🔗 {issue['html_url']}"
                ),
            }

        except Exception as e:
            return {"response_type": "ephemeral", "text": f"❌ Failed to get issue: {str(e)}"}

    def _handle_status_command(self):
        """Handle status command."""
        return {
            "response_type": "in_channel",
            "text": (
                "🤖 **DiceBot Status**\n"
                "✅ Vercel: Online\n"
                "🔗 GitHub: Connected\n"
                "💬 Slack: Connected"
            ),
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
