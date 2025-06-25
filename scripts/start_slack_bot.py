#!/usr/bin/env python3
"""
Start the DiceBot Slack server.
"""

import logging
import sys
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dicebot.integrations.slack_server import create_slack_server

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def main():
    """Main function."""
    try:
        # Create and start server
        server = create_slack_server()
        server.run(debug=False)

    except ValueError as e:
        print(f"Configuration error: {e}")
        print("\nRequired environment variables:")
        print("- SLACK_BOT_TOKEN: Your Slack bot token")
        print("- SLACK_SIGNING_SECRET: Your Slack app signing secret")
        print("- SLACK_SERVER_PORT (optional): Server port (default: 3000)")
        sys.exit(1)

    except Exception as e:
        print(f"Error starting Slack server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
