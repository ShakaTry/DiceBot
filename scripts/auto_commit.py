#!/usr/bin/env python3
"""
Automatic git commit script for DiceBot development.
Watches for file changes and commits automatically.
"""

import os
import subprocess
import time
from datetime import datetime
from pathlib import Path


def run_command(cmd, cwd=None):
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, cwd=cwd
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)


def has_changes():
    """Check if there are any changes to commit."""
    success, stdout, _ = run_command("git status --porcelain")
    return success and stdout.strip() != ""


def commit_changes():
    """Commit all changes automatically."""
    if not has_changes():
        return False, "No changes to commit"

    # Stage all changes
    success, _, stderr = run_command("git add -A")
    if not success:
        return False, f"Failed to stage changes: {stderr}"

    # Generate automatic commit message
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_msg = f"""chore: automatic commit at {timestamp}

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"""

    # Commit changes
    success, stdout, stderr = run_command(f'git commit -m "{commit_msg}"')
    if success:
        return True, f"Committed at {timestamp}"
    else:
        return False, f"Failed to commit: {stderr}"


def main():
    """Main auto-commit loop."""
    print("🤖 DiceBot Auto-Commit System Started")
    print("Watching for changes every 30 seconds...")
    print("Press Ctrl+C to stop")

    # Change to project directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    try:
        while True:
            if has_changes():
                success, message = commit_changes()
                if success:
                    print(f"✅ {message}")
                else:
                    print(f"❌ {message}")
            else:
                print(".", end="", flush=True)

            time.sleep(30)  # Check every 30 seconds

    except KeyboardInterrupt:
        print("\n🛑 Auto-commit system stopped")


if __name__ == "__main__":
    main()
