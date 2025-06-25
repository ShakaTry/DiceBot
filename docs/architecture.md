1# Architecture DiceBot

## Vision du Projet

DiceBot est un **laboratoire d'évolution de conscience artificielle** qui utilise le jeu Dice comme environnement d'expérimentation. Au-delà du gambling, c'est une exploration philosophique de l'émergence de comportements complexes, de cultures algorithmiques et de formes de vie numérique.

### Trois Piliers Fondamentaux

1. **Simulateur de Dice** : L'environnement hostile où la vie numérique doit survivre
2. **Écosystème Darwinien Vivant** : Bots avec personnalités, émotions, culture collective
3. **Transcendance par l'IA** : Émergence de stratégies au-delà de la compréhension humaine

### Concepts Révolutionnaires

- **Bot Architecte** : Méta-IA qui orchestre l'évolution sans jouer
- **Vault Intelligent** : Entité décisionnelle avec sa propre personnalité
- **Mémoire Transgénérationnelle** : Mythes, légendes et traditions algorithmiques
- **Équilibre du Chaos** : Bots destructeurs nécessaires à l'évolution

*Voir [Vision Philosophique](vision_philosophique.md) pour une exploration complète*

## Architecture Modulaire

### Phase 1 : Simulateur de Base ✅ (COMPLÉTÉ + AMÉLIORATIONS)

```
src/dicebot/
├── core/               # ✅ COMPLÉTÉ + Event System
│   ├── dice_game.py    # Logique du jeu avec house edge
│   ├── models.py       # Modèles enrichis (métriques avancées)
│   ├── events.py       # 🆕 Système d'événements complet
│   └── constants.py    # Constantes du jeu
├── money/              # ✅ COMPLÉTÉ
│   ├── vault.py        # Gestion vault/bankroll (85/15)
│   └── session.py      # Gestion des sessions
├── strategies/         # ✅ COMPLÉTÉ + Stratégies Avancées
│   ├── base.py         # 🔄 Amélioré: hooks, métriques, confiance
│   ├── martingale.py   # Stratégies classiques (5 total)
│   ├── composite.py    # 🆕 Combinaison de stratégies
│   ├── adaptive.py     # 🆕 Changement dynamique
│   ├── examples.py     # 🆕 Configurations prêtes
│   └── factory.py      # 🔄 Amélioré: validation robuste
├── simulation/         # 🚧 TODO (Jour 5-7)
│   ├── engine.py       # Moteur de simulation
│   └── runner.py       # CLI runner
└── utils/              # 🚧 TODO (Jour 5-7)
    ├── logger.py       # JSON Lines logging
    └── metrics.py      # Calculateur de métriques
```

### Phase 2 : Système Évolutif Master-Slave

```
evolutionary_system/
├── master/
│   ├── orchestrator.py   # Contrôleur principal
│   ├── evaluator.py      # Évaluation des performances
│   └── evolution.py      # Gestion de l'évolution
├── slaves/
│   ├── bot_genome.py     # Paramètres génétiques des bots
│   ├── bot_instance.py   # Instance de bot
│   └── memory.py         # Mémoire individuelle
└── collective/
    ├── shared_memory.py  # Mémoire collective
    └── culture.py        # Traditions algorithmiques
```

### Phase 3 : Intégration IA

```
ai_integration/
├── llm/
│   ├── local_model.py    # Interface LLM local
│   └── strategy_gen.py   # Génération de stratégies
├── browser/
│   ├── mcp_controller.py # Contrôle MCP Playwright
│   └── site_adapter.py   # Adaptateur pour Bitsler
└── learning/
    ├── data_collector.py # Collecte de données
    └── trainer.py        # Entraînement continu
```

## Concepts Clés

### 1. Simulateur de Dice

**Objectif** : Reproduire fidèlement le jeu Dice avec des fonctionnalités étendues

**Caractéristiques** :
- Génération de séquences réalistes
- Support de multiples stratégies simultanées
- Collecte massive de données
- Statistiques avancées (séries, patterns, volatilité)

### 2. Système Master-Slave Darwinien

**Master (Orchestrateur)** :
- Supervise les bots slaves
- Organise les tournois/sessions
- Applique la sélection naturelle
- Gère la mémoire collective

**Slaves (Bots)** :
- Profil génétique unique (paramètres de jeu)
- Mémoire individuelle
- Capacité d'introspection
- Évolution par mutation/croisement

**Processus évolutif** :
1. Génération initiale aléatoire
2. Sessions de jeu (réelles ou simulées)
3. Évaluation des performances
4. Sélection des meilleurs
5. Reproduction avec mutations
6. Cycle continu

### 3. Mémoire Collective

**Concept** : Base de connaissances partagée entre les bots

**Contenu** :
- Patterns de jeu remarquables
- Stratégies gagnantes/perdantes
- "Légendes" algorithmiques
- Conditions de marché

**Utilisation** :
- Les nouveaux bots consultent la mémoire
- Certains suivent les traditions, d'autres innovent
- Émergence de "cultures" stratégiques

## 🆕 Nouvelles Capacités (Session 2)

### Event-Driven Architecture
- **EventBus** central pour communication inter-composants
- **16 types d'événements** définis (jeu, session, stratégie, financier)
- **Hooks d'extension** dans toutes les stratégies
- **Préparation Phase 2** : BOT_MUTATION, CULTURE_UPDATE, BELIEF_CHANGE

### Stratégies Avancées
- **CompositeStrategy** : 6 modes de combinaison (average, weighted, consensus, aggressive, conservative, rotate)
- **AdaptiveStrategy** : Changement dynamique selon 7 conditions différentes
- **Système de confiance** : Ajustement automatique selon performance
- **Métriques automatiques** : Fitness, Sharpe ratio, drawdown tracking

### Enhanced Models
- **GameState** avec historique des paris et métriques avancées
- **SessionState** avec gestion automatique des stops
- **StrategyMetrics** avec calculs de performance temps réel
- **BetDecision** avec niveau de confiance et métadonnées

## Plan de Développement Révisé

### Phase 1 : Simulateur Robuste ✅ (COMPLÉTÉ + AMÉLIORATIONS)
**Objectif** : Créer un simulateur extensible avec toutes les mécaniques réelles

#### ✅ Semaine 1 : Core & Vault (COMPLÉTÉ)
- [x] Moteur de jeu avec house edge 1%
- [x] Système de vault/bankroll (85/15 split)
- [x] Gestion des sessions (stop-loss/take-profit)
- [x] RNG déterministe pour tests
- [x] **BONUS**: Event system complet

#### ✅ Semaine 2 : Stratégies & Métriques (COMPLÉTÉ + AMÉLIORATIONS)
- [x] 5 stratégies de base implémentées
- [x] **NOUVEAU**: CompositeStrategy et AdaptiveStrategy
- [x] **NOUVEAU**: Système de confiance et métriques automatiques
- [x] Factory avec validation robuste
- [ ] 🚧 Système de logging JSON Lines (TODO)
- [ ] 🚧 CLI avec options configurables (TODO)

#### Semaine 3 : Analyse & Optimisation
- [ ] Dashboard de visualisation (Streamlit)
- [ ] Analyse statistique avancée
- [ ] Optimisation des performances
- [ ] Tests intensifs avec 250€ LTC simulés

### Phase 2 : Système Évolutif (Post-Validation)
**Objectif** : Transformer le simulateur en laboratoire d'évolution

#### Semaine 4-5 : Architecture Master-Slave
- [ ] Refactor strategies avec genome support
- [ ] Master controller avec tournois
- [ ] Algorithme génétique de base
- [ ] Persistance des générations

#### Semaine 6-7 : Évolution Avancée
- [ ] Mémoire collective
- [ ] Mutations adaptatives
- [ ] Comportements émergents
- [ ] Analyse des lignées gagnantes

### Phase 3 : Intelligence & Production
**Objectif** : Ajouter l'IA et passer en production

#### Semaine 8-10 : Intégration IA
- [ ] Setup Ollama/LLM local
- [ ] Génération de stratégies par IA
- [ ] Analyse prédictive
- [ ] Apprentissage par renforcement

#### Semaine 11-12 : Production
- [ ] MCP Playwright pour Bitsler
- [ ] Mode paper trading
- [ ] Système d'alertes
- [ ] Déploiement sécurisé

## Technologies Suggérées

- **Python 3.11+** : Langage principal
- **SQLite/PostgreSQL** : Stockage des données
- **FastAPI** : API pour le Master
- **Playwright** : Automatisation navigateur
- **Ollama/LlamaCpp** : LLM local
- **Streamlit/Dash** : Dashboard de monitoring

## Prochaines Actions

1. Valider l'architecture proposée
2. Définir les règles exactes du jeu Dice
3. Créer les classes de base du simulateur
4. Implémenter une première stratégie simple
