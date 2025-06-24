# 📖 Guide Utilisateur DiceBot

## 🎯 Vue d'ensemble

DiceBot est un laboratoire d'évolution de conscience artificielle utilisant le jeu de dés comme environnement. Ce guide couvre l'utilisation du système de simulation avancé (Phase 1) avec **système Provably Fair** compatible Bitsler.

## 🚀 Installation Rapide

```bash
# Cloner le projet
git clone https://github.com/votre-repo/DiceBot.git
cd DiceBot

# Créer l'environnement virtuel
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou .venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -e ".[dev]"

# Vérifier l'installation
python -m DiceBot --version
```

## 🎮 Utilisation de Base

### Simulation Simple

```bash
# Simulation basique avec preset
python -m DiceBot simulate --capital 100 --strategy martingale --preset conservative

# Simulation personnalisée
python -m DiceBot simulate \
  --capital 250 \
  --strategy fibonacci \
  --base-bet 0.001 \
  --max-losses 10 \
  --sessions 50
```

### Comparaison de Stratégies

```bash
# Comparer plusieurs stratégies
python -m DiceBot compare \
  --capital 500 \
  --strategies martingale fibonacci dalembert \
  --sessions 100
```

### Analyse de Résultats

```bash
# Analyser un fichier de résultats
python -m DiceBot analyze results/strategy_Martingale_20250624_180453.json

# Analyse détaillée
python -m DiceBot analyze results/strategy_comparison_20250624_173709.json --detailed
```

## ⚙️ Configuration Avancée

### Fichier de Configuration (dicebot.yaml)

Le système utilise un fichier de configuration YAML pour personnaliser les paramètres :

```yaml
# dicebot.yaml
simulation:
  default_sessions: 100
  parallel_workers: 4
  auto_parallel_threshold: 50

strategies:
  presets:
    conservative:
      base_bet: "0.0005"
      max_losses: 5
      multiplier: 2.0
    
    moderate:
      base_bet: "0.001"
      max_losses: 8
      multiplier: 2.0

game:
  house_edge: 0.01
  min_bet_ltc: "0.00015"
  max_bet_ltc: "1000"
```

### Presets Disponibles

| Preset | Base Bet | Max Losses | Risque | Usage |
|--------|----------|------------|--------|-------|
| `conservative` | 0.0005 LTC | 5 | Faible | Débutants, capital limité |
| `moderate` | 0.001 LTC | 8 | Moyen | Usage général |
| `aggressive` | 0.002 LTC | 12 | Élevé | Expérimentés |
| `experimental` | 0.003 LTC | 15 | Extrême | Tests avancés |

## 🎯 Stratégies Disponibles

### Stratégies de Base

1. **martingale** - Double la mise après chaque perte
   - Risque : Élevé
   - Capital requis : Important
   - Usage : Court terme

2. **fibonacci** - Suit la séquence de Fibonacci
   - Risque : Modéré
   - Capital requis : Moyen
   - Usage : Polyvalent

3. **dalembert** - +1/-1 unité selon le résultat
   - Risque : Faible
   - Capital requis : Faible
   - Usage : Conservative

4. **flat** - Mise constante
   - Risque : Minimal
   - Capital requis : Minimal
   - Usage : Test de base

5. **paroli** - Double après victoire (anti-martingale)
   - Risque : Faible
   - Capital requis : Faible
   - Usage : Opportuniste

### Stratégies Avancées

6. **composite** - Combine plusieurs stratégies
7. **adaptive** - Change de stratégie dynamiquement

## 🎲 Système Provably Fair

DiceBot intègre un système **Provably Fair** 100% compatible avec Bitsler.com :

### Utilisation de Base

```bash
# Mode provably fair automatique (par défaut)
python -m DiceBot simulate --capital 100 --strategy fibonacci

# Les résultats incluent automatiquement les informations de seed
# Fichier JSON contient: server_seed_hash, client_seed, nonce pour chaque pari
```

### Vérification des Résultats

Tous les résultats peuvent être vérifiés avec l'algorithme exact de Bitsler :

```python
from dicebot.core.provably_fair import BitslerVerifier

# Vérifier un résultat
verification = BitslerVerifier.verify_dice_result(
    server_seed="révélé_après_rotation",
    client_seed="votre_seed",
    nonce=0,
    expected_result=42.15
)
print(f"Valide: {verification['is_valid']}")
```

### Compatibilité Bitsler

- ✅ **Algorithme identique** : HMAC-SHA512 + extraction par chunks
- ✅ **Vérification croisée** : Compatible avec le vérificateur officiel Bitsler  
- ✅ **Transparence totale** : Tous les résultats sont vérifiables
- ✅ **Sécurité cryptographique** : Impossible de prédire ou manipuler

📚 **Documentation complète** : Voir [PROVABLY_FAIR.md](PROVABLY_FAIR.md)

## 🚀 Fonctionnalités Avancées

### Parallélisation

```bash
# Force le mode parallèle
python -m DiceBot simulate --capital 1000 --strategy fibonacci --sessions 200 --parallel

# Auto-parallélisation (≥50 sessions)
python -m DiceBot simulate --capital 1000 --strategy martingale --sessions 100
```

### Validation et Suggestions

Le système valide automatiquement les paramètres et propose des améliorations :

```bash
python -m DiceBot simulate --capital 10 --strategy martingale --base-bet 1
# ⚠️  Warning: base_bet is 10.0% of capital - very risky
# 💡 Consider reducing base_bet to 0.100000 LTC (1% of capital)
# ⚠️  Warning: Risk level: EXTREME
```

### Système de Recovery

```bash
# Lister les checkpoints disponibles
python -m DiceBot recovery list

# Reprendre une simulation
python -m DiceBot recovery resume simulation_id_123

# Nettoyer les anciens checkpoints
python -m DiceBot recovery clean --max-age 7
```

## 📊 Interprétation des Résultats

### Métriques Principales

- **ROI** : Retour sur investissement (%)
- **Profitability Rate** : % de sessions profitables
- **Win Rate** : % de paris gagnés
- **Max Drawdown** : Plus grosse perte depuis un pic
- **Sharpe Ratio** : Ratio rendement/risque

### Exemple de Sortie

```
============================================================
SIMULATION SUMMARY
============================================================
Strategy: Martingale
Sessions completed: 100
Total bets: 45,230
Overall ROI: 2.34%
Profitable sessions: 67/100 (67.0%)
Average win rate: 49.4%
Worst drawdown: -23.5%

Vault Status:
  Final capital: 102.340000 LTC
  Net profit: 2.340000 LTC
```

## ⚠️ Gestion des Risques

### Niveaux de Risque

- **LOW** : Capital sûr, gains modérés
- **MEDIUM** : Équilibre risque/rendement
- **HIGH** : Risque élevé, gains potentiels importants
- **EXTREME** : Risque de perte totale

### Suggestions de Sécurité

1. **Commencez petit** : Testez avec 1-10 LTC
2. **Utilisez les presets** : Commencez par 'conservative'
3. **Respectez les avertissements** : Le système vous prévient
4. **Diversifiez** : Comparez plusieurs stratégies
5. **Analysez les résultats** : Étudiez avant d'investir

## 🔧 Dépannage

### Erreurs Communes

1. **"Invalid capital format"**
   ```bash
   # ❌ Incorrect
   --capital 1,000
   
   # ✅ Correct
   --capital 1000
   ```

2. **"Validation failed"**
   - Vérifiez les ratios capital/mise
   - Utilisez un preset pour commencer

3. **"Checkpoint not found"**
   ```bash
   # Lister les checkpoints disponibles
   python -m DiceBot recovery list
   ```

### Performance

- **Sessions lentes** : Utilisez `--parallel` pour ≥50 sessions
- **Mémoire limitée** : Réduisez le nombre de sessions
- **Progression cachée** : Utilisez `--no-progress` pour les scripts

## 📈 Exemples d'Usage Avancé

### Test de Paramètres

```bash
# Test conservateur pour validation
python -m DiceBot simulate \
  --capital 100 \
  --strategy fibonacci \
  --preset conservative \
  --sessions 10 \
  --quiet

# Test de performance avec parallélisme
python -m DiceBot simulate \
  --capital 1000 \
  --strategy martingale \
  --base-bet 0.001 \
  --max-losses 8 \
  --sessions 500 \
  --parallel
```

### Comparaison Complète

```bash
# Comparer toutes les stratégies de base
python -m DiceBot compare \
  --capital 1000 \
  --strategies martingale fibonacci dalembert flat paroli \
  --sessions 200
```

### Session Limitée

```bash
# Session avec stop-loss et take-profit
python -m DiceBot simulate \
  --capital 500 \
  --strategy fibonacci \
  --preset moderate \
  --stop-loss -0.1 \
  --take-profit 0.2 \
  --max-bets 1000
```

## 📞 Support

- **Documentation** : `/docs/` dans le projet
- **Tests** : `pytest tests/` pour valider l'installation
- **Issues** : Créez une issue GitHub pour les bugs
- **Logs** : Consultez `results/` pour les données détaillées

## 🎯 Prochaines Étapes

1. **Maîtrisez les presets** : Commencez par 'conservative'
2. **Analysez les résultats** : Utilisez `compare` et `analyze`
3. **Expérimentez prudemment** : Augmentez progressivement
4. **Préparez-vous à la Phase 2** : Système évolutionnaire à venir !

---

*Guide mis à jour pour DiceBot Phase 1 - Production Ready*
