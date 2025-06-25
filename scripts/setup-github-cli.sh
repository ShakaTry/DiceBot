#!/bin/bash
# Setup GitHub CLI for DiceBot project

set -e

echo "🐙 Setting up GitHub CLI for DiceBot..."

# Check if gh is installed
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI not installed"
    echo "Install with: sudo apt install gh"
    exit 1
fi

echo "✅ GitHub CLI found: $(gh --version | head -1)"

# Check authentication
if gh auth status >/dev/null 2>&1; then
    echo "✅ Already authenticated"
    gh auth status
else
    echo "🔐 Authentication required"
    echo "Running: gh auth login"
    echo ""
    echo "📋 Choose these options:"
    echo "1. GitHub.com"
    echo "2. HTTPS"
    echo "3. Yes (authenticate with browser)"
    echo "4. Login with web browser"
    echo ""
    
    # Interactive authentication
    gh auth login
fi

echo ""
echo "🎯 GitHub CLI Commands for DiceBot:"
echo ""
echo "📋 Issues:"
echo "  gh issue list                    # List issues"
echo "  gh issue create --title 'Bug'   # Create issue"
echo "  gh issue view 1                 # View issue #1"
echo "  gh issue close 1                # Close issue #1"
echo ""
echo "🔄 Pull Requests:"
echo "  gh pr list                      # List PRs"
echo "  gh pr create --title 'Feature'  # Create PR"
echo "  gh pr view 1                    # View PR #1"
echo "  gh pr merge 1                   # Merge PR #1"
echo ""
echo "🏷️ Releases:"
echo "  gh release list                 # List releases"
echo "  gh release create v1.1.0        # Create release"
echo "  gh release view v1.0.0          # View release"
echo ""
echo "🚀 Actions:"
echo "  gh workflow list                # List workflows"
echo "  gh workflow run release.yml     # Trigger workflow"
echo "  gh run list                     # List workflow runs"
echo ""
echo "🔧 Repository:"
echo "  gh repo view                    # View repo info"
echo "  gh repo clone ShakaTry/DiceBot  # Clone repo"
echo "  gh repo fork                    # Fork repo"
echo ""
echo "💡 Pro Tips:"
echo "  gh alias set prc 'pr create'    # Create aliases"
echo "  gh config set editor vim        # Set editor"
echo "  gh api repos/ShakaTry/DiceBot   # Direct API calls"
