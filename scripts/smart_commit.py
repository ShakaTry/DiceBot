#!/usr/bin/env python3
"""
Assistant de commit intelligent pour PyCharm.
Analyse les changements et propose des messages de commit appropriés.
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path


def run_git_command(cmd: str) -> str:
    """Execute une commande git et retourne la sortie."""
    try:
        result = subprocess.run(
            f"git {cmd}", shell=True, capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return ""


def analyze_changes() -> dict:
    """Analyse les changements Git pour proposer un message de commit."""
    # Fichiers modifiés
    modified = run_git_command("diff --name-only --cached").split('\n')
    modified = [f for f in modified if f]
    
    # Fichiers ajoutés
    added = run_git_command("diff --name-only --cached --diff-filter=A").split('\n')
    added = [f for f in added if f]
    
    # Statistiques
    stats = run_git_command("diff --cached --shortstat")
    
    return {
        "modified": modified,
        "added": added, 
        "stats": stats,
        "total_files": len(modified)
    }


def suggest_commit_message(changes: dict) -> str:
    """Suggère un message de commit basé sur les changements."""
    files = changes["modified"]
    
    # Analyse des types de changements
    has_tests = any("test" in f for f in files)
    has_docs = any(f.endswith(".md") for f in files)
    has_config = any(f.endswith((".yml", ".yaml", ".toml", ".json")) for f in files)
    has_python = any(f.endswith(".py") for f in files)
    has_integration = any("integration" in f for f in files)
    has_cli = any("__main__" in f for f in files)
    
    # Détermine le type de commit
    if has_tests and len(files) <= 3:
        commit_type = "test"
        description = "Add/update tests"
    elif has_docs and not has_python:
        commit_type = "docs" 
        description = "Update documentation"
    elif has_config and not has_python:
        commit_type = "config"
        description = "Update configuration"
    elif has_integration:
        commit_type = "feat"
        description = "Update integrations"
    elif has_cli:
        commit_type = "feat"
        description = "Update CLI functionality"
    elif len(changes["added"]) > 0:
        commit_type = "feat"
        description = "Add new functionality"
    else:
        commit_type = "fix"
        description = "Update existing functionality"
    
    # Message principal
    main_areas = []
    if any("slack" in f for f in files):
        main_areas.append("Slack integration")
    if any("monitor" in f for f in files):
        main_areas.append("monitoring")
    if any("strategy" in f for f in files):
        main_areas.append("strategies")
    if any("simulation" in f for f in files):
        main_areas.append("simulation")
    
    if main_areas:
        description = f"Update {', '.join(main_areas)}"
    
    # Stats
    stats_line = f"📊 {changes['stats']}" if changes['stats'] else f"📁 {changes['total_files']} files"
    
    return f"""{commit_type}: {description}

{stats_line}
⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🚀 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Smart Commit Assistant <noreply@dicebot.ai>"""


def main():
    """Fonction principale."""
    print("🤖 Smart Commit Assistant")
    
    # Vérifier s'il y a des changements staged
    if not run_git_command("diff --cached --name-only"):
        print("⚠️ Aucun changement staged. Utilise 'git add' d'abord.")
        
        # Proposer d'ajouter tous les changements
        if run_git_command("status --porcelain"):
            response = input("🔄 Ajouter tous les changements ? (y/N): ")
            if response.lower() == 'y':
                subprocess.run("git add .", shell=True)
            else:
                return 1
        else:
            print("✅ Aucun changement détecté.")
            return 0
    
    # Analyser les changements
    changes = analyze_changes()
    
    if changes["total_files"] == 0:
        print("✅ Aucun changement à committer.")
        return 0
    
    # Afficher l'analyse
    print(f"\n📊 Analyse des changements:")
    print(f"  📁 Fichiers modifiés: {changes['total_files']}")
    if changes["added"]:
        print(f"  ➕ Nouveaux fichiers: {len(changes['added'])}")
    print(f"  📈 {changes['stats']}")
    
    # Suggérer un message
    suggested_message = suggest_commit_message(changes)
    
    print(f"\n💡 Message suggéré:")
    print("-" * 50)
    print(suggested_message)
    print("-" * 50)
    
    # Demander confirmation
    response = input("\n🚀 Committer avec ce message ? (Y/n/e pour éditer): ").lower()
    
    if response == 'n':
        print("❌ Commit annulé.")
        return 1
    elif response == 'e':
        # Ouvrir l'éditeur pour éditer le message
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False) as f:
            f.write(suggested_message)
            temp_file = f.name
        
        # Ouvrir l'éditeur
        subprocess.run(f"$EDITOR {temp_file} || nano {temp_file} || vim {temp_file}", shell=True)
        
        # Lire le message édité
        with open(temp_file) as f:
            suggested_message = f.read().strip()
        
        Path(temp_file).unlink()  # Supprimer le fichier temporaire
    
    # Committer
    try:
        subprocess.run(["git", "commit", "-m", suggested_message], check=True)
        print("✅ Commit réussi!")
        
        # Proposer de push
        response = input("🚀 Push vers GitHub ? (Y/n): ").lower()
        if response != 'n':
            subprocess.run(["git", "push", "origin", "main"], check=True)
            print("🎉 Push réussi! GitHub Actions va se déclencher.")
        
        return 0
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors du commit: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())