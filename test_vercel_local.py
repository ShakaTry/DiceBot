#!/usr/bin/env python3
"""
Test script for Vercel deployment locally.
Uses environment variables from .env file.
"""

import os
import sys
from pathlib import Path

# Add src to path for local testing
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_slack_integration():
    """Test Slack → GitHub integration with environment variables."""

    # Load environment variables from .env if it exists
    env_file = Path(".env")
    if env_file.exists():
        print("📁 Loading environment variables from .env")
        with open(env_file) as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    os.environ[key] = value

    # Check required environment variables
    required_vars = ["GITHUB_TOKEN", "SLACK_BOT_TOKEN", "SLACK_SIGNING_SECRET"]

    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("📝 Create a .env file with these variables:")
        for var in missing_vars:
            print(f"   {var}=your_value_here")
        return False

    print("✅ All environment variables found")

    # Test GitHub client
    try:
        from dicebot.integrations import GitHubClient

        github_client = GitHubClient(
            token=os.getenv("GITHUB_TOKEN"),
            owner=os.getenv("GITHUB_OWNER", "ShakaTry"),
            repo=os.getenv("GITHUB_REPO", "DiceBot"),
        )

        # Test getting issues
        result = github_client.get_issues(state="open", limit=3)
        if result["success"]:
            print(f"🐙 GitHub: Connected! Found {result['count']} open issues")
        else:
            print(f"❌ GitHub error: {result['error']}")
            return False

    except Exception as e:
        print(f"❌ GitHub client error: {e}")
        return False

    # Test Slack bot
    try:
        from dicebot.integrations import SlackBot

        slack_bot = SlackBot(
            bot_token=os.getenv("SLACK_BOT_TOKEN"),
            signing_secret=os.getenv("SLACK_SIGNING_SECRET"),
            github_client=github_client,
        )

        print("💬 Slack: Bot initialized successfully")

        # Test issue command parsing
        if slack_bot.github_bridge:
            test_command = 'create "Test issue" "This is a test from local script"'
            parsed = slack_bot.github_bridge.parse_issue_command(test_command)
            print(f"🔧 Issue command parsing: {parsed['action']} - '{parsed.get('title', 'N/A')}'")

    except Exception as e:
        print(f"❌ Slack bot error: {e}")
        return False

    print("🎉 All integrations working!")
    return True


def simulate_slack_command():
    """Simulate a Slack slash command."""

    # Test data for issue creation
    test_commands = [
        ("list", "open"),
        ("create", '"Bug in Fibonacci" "Strategy fails after 10 losses"'),
        ("show", "#1"),
    ]

    print("\n🧪 Testing issue commands:")

    for cmd, args in test_commands:
        print(f"\n Testing: /issue {cmd} {args}")

        try:
            from dicebot.integrations import GitHubClient, SlackBot

            github_client = GitHubClient(
                token=os.getenv("GITHUB_TOKEN"),
                owner=os.getenv("GITHUB_OWNER", "ShakaTry"),
                repo=os.getenv("GITHUB_REPO", "DiceBot"),
            )

            slack_bot = SlackBot(
                bot_token=os.getenv("SLACK_BOT_TOKEN"),
                signing_secret=os.getenv("SLACK_SIGNING_SECRET"),
                github_client=github_client,
            )

            if slack_bot.github_bridge:
                command = slack_bot.github_bridge.parse_issue_command(f"{cmd} {args}")
                response = slack_bot.github_bridge.execute_command(command, "test_user")
                print(f"✅ Response: {response[:100]}...")

        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("🎲 DiceBot Vercel Integration Test")
    print("=" * 40)

    if test_slack_integration():
        if input("\n🧪 Run command simulation? (y/n): ").lower() == "y":
            simulate_slack_command()

    print("\n✨ Test complete!")
