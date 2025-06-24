"""
Generic webhook notifications for DiceBot events.
"""

import json
import logging
from datetime import datetime
from typing import Any

import requests


class WebhookNotifier:
    """Generic webhook notifier for external integrations."""

    def __init__(self, webhook_url: str, secret: str | None = None):
        """Initialize webhook notifier.

        Args:
            webhook_url: URL to send webhooks to
            secret: Optional secret for HMAC signing
        """
        self.webhook_url = webhook_url
        self.secret = secret
        self.logger = logging.getLogger(__name__)

    def send_webhook(self, event_type: str, data: dict[str, Any]) -> bool:
        """Send webhook notification.

        Args:
            event_type: Type of event
            data: Event data

        Returns:
            True if successful, False otherwise
        """
        try:
            payload = {
                "event_type": event_type,
                "timestamp": datetime.now().isoformat(),
                "data": data,
                "source": "dicebot",
            }

            headers = {"Content-Type": "application/json"}

            # Add HMAC signature if secret is provided
            if self.secret:
                import hashlib
                import hmac

                body = json.dumps(payload, sort_keys=True)
                signature = hmac.new(
                    self.secret.encode(), body.encode(), hashlib.sha256
                ).hexdigest()
                headers["X-DiceBot-Signature"] = f"sha256={signature}"

            response = requests.post(
                self.webhook_url, json=payload, headers=headers, timeout=10
            )
            response.raise_for_status()

            self.logger.info(f"Webhook sent successfully: {event_type}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to send webhook: {e}")
            return False

    def notify_simulation_start(
        self, strategy: str, capital: float, sessions: int
    ) -> bool:
        """Notify simulation start."""
        data = {
            "strategy": strategy,
            "capital": capital,
            "sessions": sessions,
            "status": "started",
        }
        return self.send_webhook("simulation_start", data)

    def notify_simulation_complete(self, results: dict[str, Any]) -> bool:
        """Notify simulation completion."""
        return self.send_webhook("simulation_complete", results)

    def notify_bet_result(self, bet_data: dict[str, Any]) -> bool:
        """Notify individual bet result."""
        return self.send_webhook("bet_result", bet_data)

    def notify_alert(
        self, alert_type: str, message: str, severity: str = "info"
    ) -> bool:
        """Send alert notification."""
        data = {"alert_type": alert_type, "message": message, "severity": severity}
        return self.send_webhook("alert", data)

    def notify_error(self, error: str, context: str) -> bool:
        """Notify error occurrence."""
        data = {"error": error, "context": context, "severity": "error"}
        return self.send_webhook("error", data)
