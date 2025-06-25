"""
GitHub integration for DiceBot - Create and manage issues from Slack.
"""

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import requests


@dataclass
class GitHubIssue:
    """GitHub issue data structure."""

    title: str
    body: str
    labels: list[str] = None
    assignees: list[str] = None
    milestone: int | None = None


class GitHubClient:
    """GitHub API client for issue management."""

    def __init__(self, token: str, owner: str, repo: str):
        """Initialize GitHub client.

        Args:
            token: GitHub personal access token
            owner: Repository owner (username or organization)
            repo: Repository name
        """
        self.token = token
        self.owner = owner
        self.repo = repo
        self.base_url = "https://api.github.com"
        self.logger = logging.getLogger(__name__)

        # Headers for API requests
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def create_issue(self, issue: GitHubIssue) -> dict[str, Any]:
        """Create a new GitHub issue.

        Args:
            issue: Issue data

        Returns:
            Created issue data or error info
        """
        try:
            url = f"{self.base_url}/repos/{self.owner}/{self.repo}/issues"

            payload = {"title": issue.title, "body": issue.body}

            if issue.labels:
                payload["labels"] = issue.labels
            if issue.assignees:
                payload["assignees"] = issue.assignees
            if issue.milestone:
                payload["milestone"] = issue.milestone

            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()

            created_issue = response.json()
            self.logger.info(f"Created issue #{created_issue['number']}: {issue.title}")

            return {
                "success": True,
                "issue": created_issue,
                "number": created_issue["number"],
                "url": created_issue["html_url"],
            }

        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to create GitHub issue: {e}"
            self.logger.error(error_msg)
            return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error creating issue: {e}"
            self.logger.error(error_msg)
            return {"success": False, "error": error_msg}

    def get_issues(
        self, state: str = "open", labels: str = None, limit: int = 10
    ) -> dict[str, Any]:
        """Get repository issues.

        Args:
            state: Issue state (open, closed, all)
            labels: Comma-separated list of labels to filter by
            limit: Maximum number of issues to return

        Returns:
            List of issues or error info
        """
        try:
            url = f"{self.base_url}/repos/{self.owner}/{self.repo}/issues"

            params = {
                "state": state,
                "per_page": min(limit, 100),  # GitHub API limit
                "sort": "updated",
                "direction": "desc",
            }

            if labels:
                params["labels"] = labels

            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()

            issues = response.json()

            # Filter out pull requests (GitHub API includes PRs in issues endpoint)
            issues = [issue for issue in issues if "pull_request" not in issue]

            return {"success": True, "issues": issues, "count": len(issues)}

        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to get GitHub issues: {e}"
            self.logger.error(error_msg)
            return {"success": False, "error": error_msg}

    def close_issue(self, issue_number: int, comment: str = None) -> dict[str, Any]:
        """Close a GitHub issue.

        Args:
            issue_number: Issue number to close
            comment: Optional closing comment

        Returns:
            Updated issue data or error info
        """
        try:
            # Add comment if provided
            if comment:
                comment_result = self.add_comment(issue_number, comment)
                if not comment_result["success"]:
                    return comment_result

            # Close the issue
            url = f"{self.base_url}/repos/{self.owner}/{self.repo}/issues/{issue_number}"
            payload = {"state": "closed"}

            response = requests.patch(url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()

            closed_issue = response.json()
            self.logger.info(f"Closed issue #{issue_number}")

            return {
                "success": True,
                "issue": closed_issue,
                "number": closed_issue["number"],
                "url": closed_issue["html_url"],
            }

        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to close GitHub issue #{issue_number}: {e}"
            self.logger.error(error_msg)
            return {"success": False, "error": error_msg}

    def add_comment(self, issue_number: int, comment: str) -> dict[str, Any]:
        """Add a comment to a GitHub issue.

        Args:
            issue_number: Issue number
            comment: Comment text

        Returns:
            Comment data or error info
        """
        try:
            url = f"{self.base_url}/repos/{self.owner}/{self.repo}/issues/{issue_number}/comments"
            payload = {"body": comment}

            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()

            comment_data = response.json()
            self.logger.info(f"Added comment to issue #{issue_number}")

            return {"success": True, "comment": comment_data, "url": comment_data["html_url"]}

        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to add comment to issue #{issue_number}: {e}"
            self.logger.error(error_msg)
            return {"success": False, "error": error_msg}

    def get_issue(self, issue_number: int) -> dict[str, Any]:
        """Get a specific GitHub issue.

        Args:
            issue_number: Issue number

        Returns:
            Issue data or error info
        """
        try:
            url = f"{self.base_url}/repos/{self.owner}/{self.repo}/issues/{issue_number}"

            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()

            issue = response.json()

            return {
                "success": True,
                "issue": issue,
                "number": issue["number"],
                "title": issue["title"],
                "state": issue["state"],
                "url": issue["html_url"],
            }

        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to get GitHub issue #{issue_number}: {e}"
            self.logger.error(error_msg)
            return {"success": False, "error": error_msg}

    def add_labels(self, issue_number: int, labels: list[str]) -> dict[str, Any]:
        """Add labels to a GitHub issue.

        Args:
            issue_number: Issue number
            labels: List of label names

        Returns:
            Updated labels or error info
        """
        try:
            url = f"{self.base_url}/repos/{self.owner}/{self.repo}/issues/{issue_number}/labels"
            payload = {"labels": labels}

            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()

            updated_labels = response.json()
            self.logger.info(f"Added labels {labels} to issue #{issue_number}")

            return {"success": True, "labels": updated_labels}

        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to add labels to issue #{issue_number}: {e}"
            self.logger.error(error_msg)
            return {"success": False, "error": error_msg}


class SlackGitHubBridge:
    """Bridge between Slack and GitHub for issue management."""

    def __init__(self, github_client: GitHubClient):
        """Initialize Slack-GitHub bridge.

        Args:
            github_client: Configured GitHub client
        """
        self.github = github_client
        self.logger = logging.getLogger(__name__)

    def parse_issue_command(self, text: str) -> dict[str, Any]:
        """Parse Slack issue command.

        Args:
            text: Command text from Slack

        Returns:
            Parsed command data
        """
        # Commands:
        # /issue create "Title here" "Optional body"
        # /issue list [open|closed|all]
        # /issue close #42 "Optional comment"
        # /issue comment #42 "Comment text"
        # /issue show #42

        parts = text.strip().split()
        if not parts:
            return {"action": "help"}

        action = parts[0].lower()

        if action == "create":
            return self._parse_create_command(parts[1:])
        elif action == "list":
            state = parts[1] if len(parts) > 1 else "open"
            return {"action": "list", "state": state}
        elif action == "close":
            return self._parse_close_command(parts[1:])
        elif action == "comment":
            return self._parse_comment_command(parts[1:])
        elif action == "show":
            return self._parse_show_command(parts[1:])
        else:
            return {"action": "help"}

    def _parse_create_command(self, parts: list[str]) -> dict[str, Any]:
        """Parse create issue command."""
        if not parts:
            return {"action": "error", "message": "Missing issue title"}

        # Join all parts and parse quoted strings
        text = " ".join(parts)

        # Extract quoted strings
        quoted_parts = re.findall(r'"([^"]*)"', text)

        if not quoted_parts:
            # No quotes, treat everything as title
            return {"action": "create", "title": text, "body": ""}

        title = quoted_parts[0]
        body = quoted_parts[1] if len(quoted_parts) > 1 else ""

        # Extract labels if any
        labels = []
        label_match = re.search(r"--labels?\s+([^\s]+)", text)
        if label_match:
            labels = [label.strip() for label in label_match.group(1).split(",")]

        return {"action": "create", "title": title, "body": body, "labels": labels}

    def _parse_close_command(self, parts: list[str]) -> dict[str, Any]:
        """Parse close issue command."""
        if not parts:
            return {"action": "error", "message": "Missing issue number"}

        # Extract issue number
        issue_ref = parts[0]
        issue_number = self._extract_issue_number(issue_ref)

        if issue_number is None:
            return {"action": "error", "message": "Invalid issue number"}

        # Extract comment if provided
        text = " ".join(parts)
        quoted_parts = re.findall(r'"([^"]*)"', text)
        comment = quoted_parts[0] if quoted_parts else None

        return {"action": "close", "issue_number": issue_number, "comment": comment}

    def _parse_comment_command(self, parts: list[str]) -> dict[str, Any]:
        """Parse comment on issue command."""
        if len(parts) < 2:
            return {"action": "error", "message": "Missing issue number or comment"}

        issue_ref = parts[0]
        issue_number = self._extract_issue_number(issue_ref)

        if issue_number is None:
            return {"action": "error", "message": "Invalid issue number"}

        # Extract comment
        text = " ".join(parts[1:])
        quoted_parts = re.findall(r'"([^"]*)"', text)
        comment = quoted_parts[0] if quoted_parts else text

        return {"action": "comment", "issue_number": issue_number, "comment": comment}

    def _parse_show_command(self, parts: list[str]) -> dict[str, Any]:
        """Parse show issue command."""
        if not parts:
            return {"action": "error", "message": "Missing issue number"}

        issue_ref = parts[0]
        issue_number = self._extract_issue_number(issue_ref)

        if issue_number is None:
            return {"action": "error", "message": "Invalid issue number"}

        return {"action": "show", "issue_number": issue_number}

    def _extract_issue_number(self, issue_ref: str) -> int | None:
        """Extract issue number from reference (#42, 42, etc.)."""
        # Remove # if present
        issue_ref = issue_ref.lstrip("#")

        try:
            return int(issue_ref)
        except ValueError:
            return None

    def execute_command(self, command: dict[str, Any], user: str) -> str:
        """Execute parsed issue command.

        Args:
            command: Parsed command from parse_issue_command
            user: Slack user who issued command

        Returns:
            Response message for Slack
        """
        action = command.get("action")

        if action == "create":
            return self._execute_create(command, user)
        elif action == "list":
            return self._execute_list(command)
        elif action == "close":
            return self._execute_close(command, user)
        elif action == "comment":
            return self._execute_comment(command, user)
        elif action == "show":
            return self._execute_show(command)
        elif action == "error":
            return f"❌ {command.get('message', 'Unknown error')}"
        else:
            return self._get_help_message()

    def _execute_create(self, command: dict[str, Any], user: str) -> str:
        """Execute create issue command."""
        title = command.get("title", "").strip()
        if not title:
            return "❌ Issue title cannot be empty"

        # Create issue body with Slack user attribution
        body_parts = []
        if command.get("body"):
            body_parts.append(command["body"])

        body_parts.append(
            f"\n---\n📝 Created from Slack by @{user} on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        issue = GitHubIssue(
            title=title, body="\n".join(body_parts), labels=command.get("labels", [])
        )

        result = self.github.create_issue(issue)

        if result["success"]:
            return (
                f"✅ **Issue Created Successfully!**\n"
                f"🔗 **#{result['number']}**: {title}\n"
                f"📎 {result['url']}\n"
                f"👤 Created by: @{user}"
            )
        else:
            return f"❌ Failed to create issue: {result['error']}"

    def _execute_list(self, command: dict[str, Any]) -> str:
        """Execute list issues command."""
        state = command.get("state", "open")
        if state not in ["open", "closed", "all"]:
            state = "open"

        result = self.github.get_issues(state=state, limit=10)

        if not result["success"]:
            return f"❌ Failed to get issues: {result['error']}"

        issues = result["issues"]
        if not issues:
            return f"📂 No {state} issues found"

        lines = [f"📋 **{state.title()} Issues ({len(issues)}):**"]

        for issue in issues[:10]:  # Limit to 10 for Slack readability
            state_emoji = "🟢" if issue["state"] == "open" else "🔴"
            labels = ", ".join([f"`{label['name']}`" for label in issue.get("labels", [])])
            labels_text = f" [{labels}]" if labels else ""

            lines.append(
                f"{state_emoji} **#{issue['number']}**: {issue['title'][:50]}"
                f"{'...' if len(issue['title']) > 50 else ''}{labels_text}"
            )

        return "\n".join(lines)

    def _execute_close(self, command: dict[str, Any], user: str) -> str:
        """Execute close issue command."""
        issue_number = command["issue_number"]
        comment = command.get("comment")

        # Add user attribution to comment
        if comment:
            comment = f"{comment}\n\n---\n🔒 Closed from Slack by @{user} on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        else:
            comment = (
                f"🔒 Closed from Slack by @{user} on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )

        result = self.github.close_issue(issue_number, comment)

        if result["success"]:
            return (
                f"✅ **Issue Closed Successfully!**\n"
                f"🔒 **#{result['number']}** is now closed\n"
                f"📎 {result['url']}\n"
                f"👤 Closed by: @{user}"
            )
        else:
            return f"❌ Failed to close issue #{issue_number}: {result['error']}"

    def _execute_comment(self, command: dict[str, Any], user: str) -> str:
        """Execute comment on issue command."""
        issue_number = command["issue_number"]
        comment = command["comment"]

        # Add user attribution
        comment = f"{comment}\n\n---\n💬 Comment from Slack by @{user} on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        result = self.github.add_comment(issue_number, comment)

        if result["success"]:
            return (
                f"✅ **Comment Added Successfully!**\n"
                f"💬 Added comment to **#{issue_number}**\n"
                f"📎 {result['url']}\n"
                f"👤 By: @{user}"
            )
        else:
            return f"❌ Failed to add comment to issue #{issue_number}: {result['error']}"

    def _execute_show(self, command: dict[str, Any]) -> str:
        """Execute show issue command."""
        issue_number = command["issue_number"]

        result = self.github.get_issue(issue_number)

        if not result["success"]:
            return f"❌ Failed to get issue #{issue_number}: {result['error']}"

        issue = result["issue"]
        state_emoji = "🟢" if issue["state"] == "open" else "🔴"

        # Format labels
        labels = ", ".join([f"`{label['name']}`" for label in issue.get("labels", [])])
        labels_text = f"\n🏷️ **Labels**: {labels}" if labels else ""

        # Format assignees
        assignees = ", ".join([f"@{assignee['login']}" for assignee in issue.get("assignees", [])])
        assignees_text = f"\n👤 **Assignees**: {assignees}" if assignees else ""

        # Truncate body for Slack
        body = issue.get("body", "").strip()
        if len(body) > 300:
            body = body[:300] + "..."

        description_text = f"\n\n**Description:**\n{body}" if body else ""

        return (
            f"{state_emoji} **Issue #{issue['number']}: {issue['title']}**\n"
            f"📅 **Created**: {issue['created_at'][:10]}\n"
            f"📝 **State**: {issue['state'].title()}"
            f"{labels_text}"
            f"{assignees_text}\n"
            f"🔗 {issue['html_url']}"
            f"{description_text}"
        )

    def _get_help_message(self) -> str:
        """Get help message for issue commands."""
        return (
            "🤖 **DiceBot GitHub Issues Help**\n\n"
            "**Commands:**\n"
            '`/issue create "Title" "Body"` - Create new issue\n'
            "`/issue list [open|closed|all]` - List issues\n"
            "`/issue show #42` - Show issue details\n"
            '`/issue close #42 "Comment"` - Close issue\n'
            '`/issue comment #42 "Text"` - Add comment\n\n'
            "**Examples:**\n"
            '`/issue create "Bug in Fibonacci strategy" "Strategy fails after 10 losses"`\n'
            '`/issue close #15 "Fixed in latest update"`\n'
            "`/issue list closed`"
        )
