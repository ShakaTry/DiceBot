#!/bin/bash
# Setup GitHub CLI aliases for DiceBot

echo "🎯 Setting up GitHub CLI aliases for DiceBot..."

# Check if authenticated
if ! gh auth status >/dev/null 2>&1; then
    echo "❌ Please authenticate first: gh auth login"
    exit 1
fi

# === REPOSITORY ALIASES ===
gh alias set repo-status 'repo view ShakaTry/DiceBot'
gh alias set repo-issues 'issue list --repo ShakaTry/DiceBot'
gh alias set repo-prs 'pr list --repo ShakaTry/DiceBot'

# === ISSUE ALIASES ===
gh alias set bug 'issue create --label bug --assignee @me --title'
gh alias set feature 'issue create --label enhancement --assignee @me --title'
gh alias set issue-mine 'issue list --assignee @me'

# === PR ALIASES ===
gh alias set prc 'pr create --assignee @me'
gh alias set prv 'pr view'
gh alias set prm 'pr merge'
gh alias set pr-mine 'pr list --author @me'

# === WORKFLOW ALIASES ===
gh alias set workflows 'workflow list'
gh alias set runs 'run list --limit 10'
gh alias set run-watch 'run watch'

# === RELEASE ALIASES ===
gh alias set releases 'release list'
gh alias set release-create 'release create'
gh alias set release-view 'release view'

# === DICEBOT SPECIFIC ===
gh alias set dice-simulate '!gh workflow run dicebot-production.yml'
gh alias set dice-release '!gh workflow run release.yml'
gh alias set dice-status '!echo "🎲 DiceBot Status:" && gh repo view ShakaTry/DiceBot && echo "" && gh run list --limit 3'

echo "✅ Aliases created!"
echo ""
echo "🎯 Available aliases:"
echo ""
echo "📋 Repository:"
echo "  gh repo-status          # View repo"
echo "  gh repo-issues          # List issues"
echo "  gh repo-prs             # List PRs"
echo ""
echo "🐛 Issues:"
echo "  gh bug 'Title'          # Create bug"
echo "  gh feature 'Title'      # Create feature"
echo "  gh issue-mine           # My issues"
echo ""
echo "🔄 Pull Requests:"
echo "  gh prc                  # Create PR"
echo "  gh prv 1                # View PR #1"
echo "  gh prm 1                # Merge PR #1"
echo "  gh pr-mine              # My PRs"
echo ""
echo "🚀 Workflows:"
echo "  gh workflows            # List workflows"
echo "  gh runs                 # Recent runs"
echo "  gh run-watch            # Watch current run"
echo ""
echo "🏷️ Releases:"
echo "  gh releases             # List releases"
echo "  gh release-create v1.1.0  # Create release"
echo ""
echo "🎲 DiceBot Specific:"
echo "  gh dice-simulate        # Trigger simulation"
echo "  gh dice-release         # Trigger release"
echo "  gh dice-status          # Full status"
echo ""
echo "💡 Use 'gh alias list' to see all aliases"
