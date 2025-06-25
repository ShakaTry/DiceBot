#!/bin/bash
# Script d'auto-commit pour PyCharm File Watcher

# Attendre 2 secondes pour éviter les commits trop fréquents
sleep 2

# Aller dans le répertoire du projet
cd "$(dirname "$0")/.."

# Vérifier s'il y a des changements
if [ -n "$(git status --porcelain)" ]; then
    echo "🔄 Auto-committing changes..."
    
    # Ajouter tous les fichiers
    git add .
    
    # Commit avec message automatique
    git commit -m "auto: Auto-commit from PyCharm

🔄 Changes detected and committed automatically
📁 Modified files: $(git diff --cached --name-only | tr '\n' ', ')
⏰ $(date)

🚀 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: PyCharm Auto-Commit <noreply@jetbrains.com>"
    
    # Push vers GitHub
    git push origin main
    
    echo "✅ Auto-commit and push completed!"
else
    echo "✅ No changes to commit"
fi
