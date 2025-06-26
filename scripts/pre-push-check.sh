#!/bin/bash
# Script de vérification COMPLET avant push

echo "🔍 Running COMPLETE pre-push checks..."

# Activer l'environnement virtuel si nécessaire
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# 1. Ruff check
echo "📋 Running ruff check..."
ruff check src tests || exit 1

# 2. Ruff format
echo "🎨 Running ruff format check..."
ruff format --check src tests || exit 1

# 3. Type checking
echo "🔒 Running pyright..."
pyright src tests || exit 1

# 4. Tests avec coverage
echo "🧪 Running tests with coverage (90% minimum)..."
pytest --cov=dicebot --cov-fail-under=90 -x || exit 1

# 5. Security - Bandit
echo "🛡️ Running bandit security check..."
bandit -r src/ || exit 1

# 6. Security - Safety
echo "🔐 Running safety dependency check..."
safety check || exit 1

# 7. Build check
echo "📦 Checking build..."
python -m build --wheel > /dev/null 2>&1 || exit 1

# 8. Pre-commit hooks (final check)
echo "🪝 Running pre-commit hooks..."
pre-commit run --all-files || exit 1

echo "✅ ALL checks passed! Ready to commit and push."
echo "⏱️  Total checks completed successfully!"
