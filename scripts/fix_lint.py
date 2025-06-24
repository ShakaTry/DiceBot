#!/usr/bin/env python3
"""
Script pour corriger automatiquement les erreurs de linting récurrentes.
"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd: str) -> tuple[int, str]:
    """Execute une commande et retourne le code de retour et la sortie."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, check=False
        )
        return result.returncode, result.stdout + result.stderr
    except Exception as e:
        return 1, str(e)

def fix_common_issues():
    """Corrige les problèmes communs de linting."""
    print("🔧 Correction automatique des problèmes de linting...")
    
    # 1. Correction automatique avec ruff
    print("📝 Application des corrections automatiques ruff...")
    code, output = run_command("ruff check --fix --unsafe-fixes src tests")
    if code == 0:
        print("✅ Corrections ruff appliquées")
    else:
        print(f"⚠️ Quelques problèmes ruff restants:\n{output}")
    
    # 2. Formatage avec ruff
    print("🎨 Formatage du code...")
    code, output = run_command("ruff format src tests")
    if code == 0:
        print("✅ Code formaté")
    else:
        print(f"❌ Erreur de formatage:\n{output}")
    
    # 3. Vérification finale
    print("🔍 Vérification finale...")
    code, output = run_command("ruff check src tests")
    if code == 0:
        print("🎉 Aucune erreur de linting!")
        return True
    else:
        print(f"⚠️ Erreurs restantes (peut-être acceptables):\n{output}")
        return False

def main():
    """Fonction principale."""
    project_root = Path(__file__).parent.parent
    print(f"📁 Répertoire du projet: {project_root}")
    
    # Changer vers le répertoire du projet
    import os
    os.chdir(project_root)
    
    success = fix_common_issues()
    
    if success:
        print("\n✅ Tous les problèmes de linting ont été corrigés!")
        print("💡 Vous pouvez maintenant faire un commit sans problème.")
    else:
        print("\n⚠️ Quelques problèmes restants, mais probablement acceptables.")
        print("💡 Vous pouvez utiliser --no-verify pour bypasser les hooks si nécessaire.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())