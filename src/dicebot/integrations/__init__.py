"""
Integrations module for external services (Slack, webhooks, monitoring).
"""

from .github_integration import GitHubClient, GitHubIssue, SlackGitHubBridge
from .monitoring import PerformanceMonitor
from .slack_bot import SlackBot, SlackNotifier
from .webhook import WebhookNotifier

__all__ = [
    "SlackBot",
    "SlackNotifier",
    "WebhookNotifier",
    "PerformanceMonitor",
    "GitHubClient",
    "GitHubIssue",
    "SlackGitHubBridge",
]
