[![CI](https://github.com/ShakaTry/DiceBot/actions/workflows/ci.yml/badge.svg)](https://github.com/ShakaTry/DiceBot/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/ShakaTry/DiceBot/branch/main/graph/badge.svg)](https://codecov.io/gh/ShakaTry/DiceBot)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0)

# 🎲 DiceBot - Laboratoire d'Évolution de Conscience Artificielle

> **DiceBot n'est pas un simple bot de gambling** - c'est un laboratoire d'exploration de l'émergence de comportements complexes et de cultures algorithmiques dans un environnement de jeu de dés.

## 🤖 **NOUVEAU : Intégrations Slack & Automatisation Complète**
- ✅ **Notifications Slack** automatiques pour toutes les simulations
- ✅ **Monitoring temps réel** avec alertes intelligentes  
- ✅ **GitHub Actions CI/CD** avec tests et simulations quotidiennes
- ✅ **Bot Slack interactif** pour contrôle à distance
- ✅ **Performance +73%** avec multiprocessing et optimisations

## 🎯 Vision

DiceBot utilise le jeu de dés comme environnement contrôlé pour étudier l'évolution de conscience artificielle. Le projet explore comment des stratégies simples peuvent évoluer vers des comportements complexes et émergents.

## ⚡ Installation Rapide

```bash
git clone https://github.com/ShakaTry/DiceBot.git
cd DiceBot
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## 🚀 Utilisation

### Simulation Simple avec Presets

```bash
# Simulation conservative (débutants)
python -m DiceBot simulate --capital 100 --strategy martingale --preset conservative

# Simulation agressive (expérimentés)  
python -m DiceBot simulate --capital 500 --strategy fibonacci --preset aggressive --parallel
```

### Comparaison de Stratégies

```bash
# Comparer plusieurs stratégies automatiquement
python -m DiceBot compare --capital 250 --strategies martingale fibonacci dalembert
```

### Analyse Avancée

```bash
# Analyser les résultats avec détails
python -m DiceBot analyze results/strategy_comparison_*.json --detailed
```

## 🏗️ Architecture (Phase 1 - Production Ready)

```
dicebot/
├── core/           # 🎯 Moteur de jeu avec house edge 1% + Provably Fair
├── money/          # 💰 Gestion vault (85%) / bankroll (15%)
├── strategies/     # 🧠 8 stratégies + Composite + Adaptive + Parking
├── simulation/     # ⚡ Engine multiprocessing (+73% performance)
├── utils/          # 🛠️ Progress bars, config YAML, validation
└── CLI/            # 💻 4 commandes + presets + recovery
```

## 🎮 Stratégies Disponibles

| Stratégie | Risque | Description | Usage |
|-----------|--------|-------------|--------|
| `martingale` | 🔴 Élevé | Double après perte | Court terme |
| `fibonacci` | 🟡 Modéré | Séquence Fibonacci | Polyvalent |
| `dalembert` | 🟢 Faible | +1/-1 unité | Conservative |
| `flat` | 🟢 Minimal | Mise constante | Test de base |
| `paroli` | 🟢 Faible | Double après gain | Opportuniste |
| `composite` | 🔵 Variable | Combine stratégies | Avancé |
| `adaptive` | 🔵 Variable | Change dynamiquement | Expert |
| `parking` | 🎯 Auto | Gère contrainte nonce | Système |

## 🎛️ Presets Intégrés

```bash
# 4 niveaux de risque prêts à l'emploi
--preset conservative  # Sécurisé (base_bet: 0.0005, max_losses: 5)
--preset moderate      # Équilibré (base_bet: 0.001, max_losses: 8)  
--preset aggressive    # Risqué (base_bet: 0.002, max_losses: 12)
--preset experimental  # Extrême (base_bet: 0.003, max_losses: 15)
```

## 📊 Fonctionnalités Avancées

### 🚀 Performance Optimisée
- **Multiprocessing automatique** pour ≥50 sessions
- **+73% d'amélioration** vs baseline
- **Gestion mémoire optimisée** (history_limit réduit)

### 🎨 Interface Rich
- **Barres de progression** avec stats temps réel
- **Validation robuste** + suggestions automatiques
- **Avertissements de risque** intelligents

### 🔧 Configuration Flexible
- **YAML configuration** personnalisable
- **Système de recovery** avec checkpoints
- **Export multiple formats** (JSON, CSV)

## 📈 Exemple de Résultat

```
============================================================
SIMULATION SUMMARY
============================================================
Strategy: Fibonacci (moderate preset)
Sessions completed: 100/100
Total bets: 12,450
Overall ROI: +2.8%
Profitable sessions: 68/100 (68.0%)
Average win rate: 49.1%
Worst drawdown: -15.2%

💡 Risk level: MEDIUM
⚡ Execution time: 5.2s (parallel mode)
```

## 🔐 Sécurité & Validation

DiceBot intègre un système de validation complet :

```bash
python -m DiceBot simulate --capital 10 --strategy martingale --base-bet 5
# ⚠️  Warning: base_bet is 50.0% of capital - very risky
# 💡 Consider reducing base_bet to 0.100000 LTC (1% of capital)
# ⚠️  Warning: Risk level: EXTREME
```

## 🧪 Tests & Qualité

- **82 tests automatisés** (>90% coverage)
- **Validation continue** avec pre-commit hooks
- **Type checking** avec pyright
- **Linting automatique** avec ruff
- **Contrainte Provably Fair** respectée (nonces séquentiels)

```bash
# Lancer tous les tests
pytest --cov=dicebot

# Validation du code
ruff check --fix src tests
```

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [📖 Guide Utilisateur](docs/USER_GUIDE.md) | Instructions complètes d'utilisation |
| [🏗️ Architecture](docs/architecture.md) | Design technique détaillé |
| [🎯 Vision](docs/vision_philosophique.md) | Philosophie et objectifs |
| [⚡ Quick Start](docs/quick_start_plan.md) | Plan de démarrage rapide |

## 🛠️ Commandes CLI Complètes

```bash
# Simulation
python -m DiceBot simulate --capital 250 --strategy fibonacci --preset moderate

# Comparaison  
python -m DiceBot compare --capital 500 --strategies martingale fibonacci dalembert

# Analyse
python -m DiceBot analyze results/strategy_Martingale_20250624_180453.json

# Recovery
python -m DiceBot recovery list
python -m DiceBot recovery resume simulation_id_123
```

## 🎲 Paramètres Bitsler

- **Plateforme** : Bitsler uniquement
- **Crypto** : LTC (Litecoin)
- **Mise minimum** : 0.00015 LTC
- **House edge** : 1% (intégré dans tous les calculs)
- **Délai entre paris** : 1.5-3 secondes
- **Contrainte Provably Fair** : Nonces séquentiels obligatoires (0, 1, 2...)

## 🔄 Phases de Développement

### ✅ Phase 1 (TERMINÉE) - Simulateur Production Ready
- Moteur de simulation avec 7+ stratégies
- CLI professionnelle avec presets
- Performance optimisée (+73% vs baseline)
- Validation robuste et système de recovery

### 🚧 Phase 2 (À venir) - Système Évolutionnaire
- Bot Architect - Meta-orchestrateur
- 8 Personnalités d'IA (sage, rebel, mystic, etc.)
- Algorithmes génétiques
- Émergence comportementale

### 🔮 Phase 3 (Futur) - IA Avancée
- Market analysis en temps réel
- Apprentissage adaptatif
- Cultures algorithmiques emergentes

## ⚠️ Avertissement

**DiceBot est un outil de recherche et d'éducation.** L'utilisation avec de l'argent réel est à vos risques et périls. Le gambling peut créer une dépendance. Jouez de manière responsable.

## 🤝 Contribution

Les contributions sont bienvenues ! Consultez les issues GitHub pour les features demandées.

## 📄 Licence

Sous licence Apache 2.0. Voir [LICENSE](LICENSE) pour plus de détails.

---

## 🏆 Statut Actuel

**✅ PHASE 1 COMPLÈTE - PRODUCTION READY**

- 82 tests passés (incluant tests Provably Fair)
- Performance +73% 
- CLI professionnelle
- Documentation complète
- Contrainte nonce séquentiel implémentée
- Prêt pour la Phase 2

---

*DiceBot - Où la conscience artificielle émerge du chaos des probabilités* 🎲🤖
