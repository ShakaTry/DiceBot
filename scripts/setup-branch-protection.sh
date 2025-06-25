#!/bin/bash
# Setup Branch Protection Rules for DiceBot

set -e

echo "🛡️ Setting up Branch Protection for main branch..."

# Check if gh CLI is configured
if ! gh auth status >/dev/null 2>&1; then
    echo "❌ GitHub CLI not authenticated."
    echo "Please run: gh auth login"
    echo ""
    echo "📋 Manual setup instead:"
    echo "1. Go to: https://github.com/ShakaTry/DiceBot/settings/branches"
    echo "2. Click 'Add rule'"
    echo "3. Branch name pattern: main"
    echo "4. Enable required status checks:"
    echo "   - 🧪 Quality Gates"
    echo "   - 🧪 Tests & Coverage"
    echo "   - 🔒 Security Scan"
    echo "5. Enable 'Require a pull request before merging'"
    echo "6. Set required reviews to 0 (solo work)"
    exit 1
fi

echo "✅ GitHub CLI authenticated"

# Apply branch protection
echo "🔧 Applying branch protection rules..."
gh api --method PUT repos/ShakaTry/DiceBot/branches/main/protection \
    --input .github/branch-protection.json

echo "✅ Branch protection configured!"
echo ""
echo "🎯 What this means:"
echo "- ❌ No direct pushes to main"
echo "- ✅ All changes via Pull Requests"
echo "- ✅ Tests must pass before merge"
echo "- ✅ Auto-delete feature branches after merge"
echo ""
echo "📝 Development workflow:"
echo "1. git checkout -b feature/name"
echo "2. ... make changes ..."
echo "3. git push origin feature/name"
echo "4. gh pr create --title 'Description'"
echo "5. Merge via GitHub after tests pass"
