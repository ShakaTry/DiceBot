import os
from datetime import datetime

import requests
from flask import Flask, jsonify, request

app = Flask(__name__)


# Health check endpoint
@app.route("/")
def health():
    return jsonify(
        {
            "message": "DiceBot Railway Server",
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "platform": "railway",
        }
    )


# Slack webhook endpoint
@app.route("/slack/webhook", methods=["POST"])
def slack_webhook():
    try:
        data = request.get_json() or request.form.to_dict()

        # Slack slash command handling
        if "command" in data:
            command = data["command"]
            text = data.get("text", "")
            user = data.get("user_name", "unknown")

            if command == "/dicebot-status":
                return jsonify(
                    {
                        "response_type": "in_channel",
                        "text": "✅ DiceBot Railway Server Status",
                        "attachments": [
                            {
                                "color": "good",
                                "fields": [
                                    {"title": "Platform", "value": "Railway", "short": True},
                                    {"title": "Status", "value": "Online", "short": True},
                                    {"title": "User", "value": user, "short": True},
                                    {
                                        "title": "Timestamp",
                                        "value": datetime.now().isoformat(),
                                        "short": True,
                                    },
                                ],
                            }
                        ],
                    }
                )

            elif command == "/issue":
                if text.startswith("list"):
                    return handle_issue_list()
                elif text.startswith("create"):
                    return handle_issue_create(text)
                else:
                    return jsonify({"text": "Usage: `/issue list` or `/issue create <title>`"})

        return jsonify({"message": "Webhook received", "data": data})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def handle_issue_list():
    """List GitHub issues"""
    github_token = os.getenv("GITHUB_TOKEN")
    github_repo = os.getenv("GITHUB_REPO", "ShakaTry/DiceBot")

    if not github_token:
        return jsonify({"text": "❌ GitHub token not configured"})

    try:
        url = f"https://api.github.com/repos/{github_repo}/issues"
        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json",
        }

        response = requests.get(url, headers=headers)
        issues = response.json()

        if not issues:
            return jsonify({"text": "📝 No open issues found"})

        issue_list = "📋 **Open Issues:**\n"
        for issue in issues[:5]:  # Limit to 5 issues
            issue_list += f"• #{issue['number']}: {issue['title']}\n"

        return jsonify({"response_type": "in_channel", "text": issue_list})

    except Exception as e:
        return jsonify({"text": f"❌ Error fetching issues: {str(e)}"})


def handle_issue_create(text):
    """Create GitHub issue"""
    github_token = os.getenv("GITHUB_TOKEN")
    github_repo = os.getenv("GITHUB_REPO", "ShakaTry/DiceBot")

    if not github_token:
        return jsonify({"text": "❌ GitHub token not configured"})

    # Extract title from command
    title = text.replace("create", "").strip()
    if not title:
        return jsonify({"text": "❌ Please provide an issue title"})

    try:
        url = f"https://api.github.com/repos/{github_repo}/issues"
        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json",
        }

        data = {"title": title, "body": "Created via Slack command", "labels": ["slack-created"]}

        response = requests.post(url, headers=headers, json=data)
        issue = response.json()

        issue_text = f"✅ Issue created: #{issue['number']} - {issue['title']}\n{issue['html_url']}"
        return jsonify({"response_type": "in_channel", "text": issue_text})

    except Exception as e:
        return jsonify({"text": f"❌ Error creating issue: {str(e)}"})


# Test endpoints
@app.route("/test")
def test():
    return jsonify(
        {
            "message": "Railway test endpoint",
            "env_vars": {
                "GITHUB_TOKEN": "configured" if os.getenv("GITHUB_TOKEN") else "missing",
                "SLACK_BOT_TOKEN": "configured" if os.getenv("SLACK_BOT_TOKEN") else "missing",
            },
        }
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
