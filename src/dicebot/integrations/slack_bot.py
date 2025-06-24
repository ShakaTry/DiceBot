"""
Slack integration for DiceBot notifications and remote control.
"""

import json
import logging
from datetime import datetime
from decimal import Decimal
from typing import Any

import requests
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


class SlackNotifier:
    """Slack webhook notifier for simple notifications."""

    def __init__(self, webhook_url: str):
        """Initialize Slack notifier.

        Args:
            webhook_url: Slack webhook URL
        """
        self.webhook_url = webhook_url
        self.logger = logging.getLogger(__name__)

    def send_notification(self, message: str, color: str = "good") -> bool:
        """Send a notification to Slack.

        Args:
            message: Message to send
            color: Color for attachment (good, warning, danger)

        Returns:
            True if successful, False otherwise
        """
        try:
            payload = {
                "attachments": [
                    {
                        "color": color,
                        "text": message,
                        "ts": int(datetime.now().timestamp()),
                    }
                ]
            }

            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            return True

        except Exception as e:
            self.logger.error(f"Failed to send Slack notification: {e}")
            return False

    def notify_simulation_start(self, strategy: str, capital: Decimal, sessions: int) -> bool:
        """Notify simulation start."""
        message = (
            f"🎲 **DiceBot Simulation Started**\n"
            f"📊 Strategy: {strategy}\n"
            f"💰 Capital: {capital} LTC\n"
            f"🔄 Sessions: {sessions}\n"
            f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        return self.send_notification(message, "good")

    def notify_simulation_complete(self, results: dict[str, Any]) -> bool:
        """Notify simulation completion with results."""
        strategy = results.get("strategy_name", "Unknown")
        sessions = results.get("sessions_run", 0)
        profit = results.get("total_profit", 0)
        win_rate = results.get("win_rate", 0)
        roi = results.get("roi", 0)

        color = "good" if profit > 0 else "danger"
        profit_emoji = "📈" if profit > 0 else "📉"

        message = (
            f"✅ **DiceBot Simulation Complete**\n"
            f"📊 Strategy: {strategy}\n"
            f"🔄 Sessions: {sessions}\n"
            f"{profit_emoji} Profit: {profit:.6f} LTC\n"
            f"🎯 Win Rate: {win_rate:.1f}%\n"
            f"📊 ROI: {roi:.2f}%\n"
            f"⏰ Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        return self.send_notification(message, color)

    def notify_alert(self, alert_type: str, message: str) -> bool:
        """Send alert notification."""
        emoji_map = {"error": "🚨", "warning": "⚠️", "success": "✅", "info": "ℹ️"}

        color_map = {
            "error": "danger",
            "warning": "warning",
            "success": "good",
            "info": "good",
        }

        emoji = emoji_map.get(alert_type, "🔔")
        color = color_map.get(alert_type, "warning")

        full_message = f"{emoji} **DiceBot Alert**\n{message}"
        return self.send_notification(full_message, color)


class SlackBot:
    """Advanced Slack bot for DiceBot control and monitoring."""

    def __init__(self, bot_token: str, signing_secret: str):
        """Initialize Slack bot.

        Args:
            bot_token: Slack bot token
            signing_secret: Slack signing secret for verification
        """
        self.client = WebClient(token=bot_token)
        self.signing_secret = signing_secret
        self.logger = logging.getLogger(__name__)

        # Command handlers
        self.commands = {
            "/dicebot-status": self.handle_status,
            "/dicebot-simulate": self.handle_simulate,
            "/dicebot-stop": self.handle_stop,
            "/dicebot-results": self.handle_results,
        }

    def handle_status(self, channel: str, user: str) -> None:
        """Handle status command."""
        try:
            # Get system status
            import psutil

            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            status_message = (
                f"🤖 **DiceBot Status**\n"
                f"💻 CPU: {cpu_percent:.1f}%\n"
                f"🧠 Memory: {memory.percent:.1f}% ({memory.used // 1024**3}GB/{memory.total // 1024**3}GB)\n"
                f"💾 Disk: {disk.percent:.1f}% ({disk.free // 1024**3}GB free)\n"
                f"⏰ Uptime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"🎲 Ready for simulations!"
            )

            self.send_message(channel, status_message)

        except Exception as e:
            self.logger.error(f"Status command failed: {e}")
            self.send_message(channel, f"❌ Failed to get status: {e}")

    def handle_simulate(self, channel: str, user: str, text: str = "") -> None:
        """Handle simulate command."""
        try:
            # Parse command parameters
            args = text.split() if text else []

            # Default parameters
            strategy = "fibonacci"
            capital = "100"
            sessions = "10"

            # Parse arguments
            i = 0
            while i < len(args):
                if args[i] == "--strategy" and i + 1 < len(args):
                    strategy = args[i + 1]
                    i += 2
                elif args[i] == "--capital" and i + 1 < len(args):
                    capital = args[i + 1]
                    i += 2
                elif args[i] == "--sessions" and i + 1 < len(args):
                    sessions = args[i + 1]
                    i += 2
                else:
                    i += 1

            # Send immediate response
            self.send_message(
                channel,
                f"🎲 Starting simulation with {strategy} strategy, {capital} LTC capital, {sessions} sessions...",
            )

            # Schedule simulation (would integrate with actual simulation runner)
            self.schedule_simulation(channel, strategy, capital, sessions)

        except Exception as e:
            self.logger.error(f"Simulate command failed: {e}")
            self.send_message(channel, f"❌ Simulation failed: {e}")

    def handle_stop(self, channel: str, user: str) -> None:
        """Handle stop command."""
        # Implementation would stop running simulations
        self.send_message(channel, "🛑 Stopping all running simulations...")

    def handle_results(self, channel: str, user: str) -> None:
        """Handle results command."""
        try:
            # Get latest results from betlog
            from pathlib import Path

            betlog_dir = Path("betlog")
            if not betlog_dir.exists():
                self.send_message(channel, "📂 No simulation results found")
                return

            # Find latest result files
            json_files = list(betlog_dir.rglob("*.json"))
            if not json_files:
                self.send_message(channel, "📂 No result files found")
                return

            latest_file = max(json_files, key=lambda f: f.stat().st_mtime)

            # Read and format results
            with open(latest_file) as f:
                results = json.load(f)

            message = self.format_results(results, latest_file.name)
            self.send_message(channel, message)

        except Exception as e:
            self.logger.error(f"Results command failed: {e}")
            self.send_message(channel, f"❌ Failed to get results: {e}")

    def format_results(self, results: dict, filename: str) -> str:
        """Format simulation results for Slack."""
        strategy = results.get("strategy_name", "Unknown")
        sessions = results.get("sessions_run", 0)
        profit = results.get("total_profit", 0)
        win_rate = results.get("win_rate", 0)
        roi = results.get("roi", 0)

        profit_emoji = "📈" if profit > 0 else "📉"

        return (
            f"📊 **Latest Results: {filename}**\n"
            f"🎯 Strategy: {strategy}\n"
            f"🔄 Sessions: {sessions}\n"
            f"{profit_emoji} Profit: {profit:.6f} LTC\n"
            f"🎯 Win Rate: {win_rate:.1f}%\n"
            f"📊 ROI: {roi:.2f}%"
        )

    def send_message(self, channel: str, message: str) -> bool:
        """Send message to Slack channel."""
        try:
            self.client.chat_postMessage(channel=channel, text=message, parse="mrkdwn")
            return True

        except SlackApiError as e:
            self.logger.error(f"Slack API error: {e}")
            return False

    def schedule_simulation(self, channel: str, strategy: str, capital: str, sessions: str) -> None:
        """Schedule a simulation to run (placeholder for actual implementation)."""
        # This would integrate with the actual simulation runner
        # For now, just send a placeholder message
        self.send_message(
            channel,
            f"⏰ Simulation scheduled: {strategy} strategy with {capital} LTC capital",
        )

    def verify_request(self, headers: dict, body: str) -> bool:
        """Verify Slack request signature."""
        import hashlib
        import hmac

        try:
            timestamp = headers.get("X-Slack-Request-Timestamp", "")
            signature = headers.get("X-Slack-Signature", "")

            if not timestamp or not signature:
                return False

            # Check timestamp (should be within 5 minutes)
            if abs(int(datetime.now().timestamp()) - int(timestamp)) > 300:
                return False

            # Verify signature
            basestring = f"v0:{timestamp}:{body}"
            computed_signature = (
                "v0="
                + hmac.new(
                    self.signing_secret.encode(), basestring.encode(), hashlib.sha256
                ).hexdigest()
            )

            return hmac.compare_digest(computed_signature, signature)

        except Exception as e:
            self.logger.error(f"Request verification failed: {e}")
            return False
