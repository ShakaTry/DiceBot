#!/bin/bash
# Quick auto-commit script for immediate use

cd "$(dirname "$0")/.."

if [[ -n $(git status --porcelain) ]]; then
    git add -A
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    git commit -m "chore: automatic commit at $timestamp

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
    echo "✅ Changes committed at $timestamp"
else
    echo "No changes to commit"
fi
