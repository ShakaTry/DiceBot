#!/bin/bash
# Setup advanced security for DiceBot

set -e

echo "🔒 Setting up Advanced Security for DiceBot..."

# Check if on GitHub
if [ ! -d ".git" ]; then
    echo "❌ Not in a Git repository"
    exit 1
fi

# Install security tools locally
echo "📦 Installing security tools..."
python -m pip install --upgrade pip
pip install bandit[toml] safety semgrep pip-audit

echo "✅ Security tools installed"

# Run initial security scan
echo "🔍 Running initial security scan..."

echo "🔒 Bandit scan..."
bandit -r src/ -f txt || true

echo "🛡️ Safety check..."
safety check || true

echo "🔍 Semgrep scan..."
semgrep --config=auto src/ || true

echo "🔐 Dependency audit..."
pip-audit || true

echo ""
echo "✅ Initial security scan complete!"
echo ""
echo "🔧 Next steps:"
echo "1. Enable GitHub Advanced Security (if private repo)"
echo "2. Review CodeQL findings in GitHub Security tab"
echo "3. Set up branch protection rules"
echo "4. Configure secret scanning alerts"
echo ""
echo "📊 Monitoring:"
echo "- CodeQL runs weekly on Sundays"
echo "- Security scans run on every PR"
echo "- Dependency scans run daily"
echo ""
echo "🔗 Resources:"
echo "- Security Policy: .github/SECURITY.md"
echo "- CodeQL Config: .github/codeql/codeql-config.yml"
echo "- Custom Queries: .github/codeql/queries/"
echo ""
echo "⚡ Quick commands:"
echo "  bandit -r src/                  # Security scan"
echo "  safety check                   # Dependency vulnerabilities"
echo "  semgrep --config=auto src/     # Static analysis"
echo "  pip-audit                      # Package vulnerabilities"
