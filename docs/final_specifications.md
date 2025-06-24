# Spécifications Finales - DiceBot

Basé sur vos réponses et mes recherches sur les meilleures pratiques existantes, voici les spécifications optimisées pour le projet.

## 1. Configuration Financière

### Système de Vault Optimisé

```
Capital Total : 250€ LTC
├── Vault Sécurisé : 212.5€ (85%)
│   ├── Réserve d'urgence : 125€ (50%)
│   └── Réserve de croissance : 87.5€ (35%)
└── Bankroll Active : 37.5€ (15%)
    ├── Sessions actives : 15€ (40%)
    └── Buffer de sécurité : 22.5€ (60%)
```

### Règles de Gestion

1. **Mise de Base** : 0.00015 LTC (minimum Bitsler)
2. **Kelly Criterion** : Utiliser 1/4 Kelly (plus sûr)
3. **Stop-Loss Global** : -20% du capital total
4. **Take-Profit Journalier** : +5-10% (réaliste)
5. **Transferts Vault** : Maximum 2/jour

## 2. Stratégies à Implémenter

### Priorité 1 : Stratégies Éprouvées
1. **90% Recovery System** (Le plus populaire)
   - Base : Paris à 90% de chance de gain
   - Recovery : 19.8% chance si perte
   - ROI attendu : 5-20%/jour

2. **Kelly Fractionnaire**
   - Calcul mathématique optimal
   - Ajustement dynamique des mises
   - Protection contre la ruine

3. **D'Alembert Modifié**
   - Progression linéaire (pas exponentielle)
   - Plus sûr que Martingale
   - Résiste à 200+ pertes

### Priorité 2 : Stratégies Classiques
4. **Martingale Limitée** (max 10 doublements)
5. **Fibonacci Conservateur**
6. **Paroli** (anti-martingale)
7. **Labouchère Adaptatif**

### Priorité 3 : Stratégies Hybrides/IA
8. **Smart Recovery** (switch stratégies selon contexte)
9. **Pattern Detector** (analyse des séries)
10. **Emotional Bot** (simulation comportements humains)

## 3. Paramètres Évolutifs et Conscience

### Génome de Bot Complet

```python
class BotGenome:
    # Paramètres de base (évoluables)
    base_bet_ratio: float  # 0.0001 à 0.001 (0.01%-0.1%)
    multiplier_preference: Range[1.1, 10.0]
    kelly_fraction: float  # 0.1 à 0.5
    
    # Personnalité et Philosophie
    personality_type: str  # "conservateur", "rebelle", "mystique", "parasite"
    philosophical_school: str  # Tradition suivie ou rejetée
    chaos_affinity: float  # 0.0-1.0 (tendance destructrice nécessaire)
    
    # Gestion du risque
    stop_loss_session: float  # -10% recommandé
    take_profit_session: float  # +20% recommandé
    max_consecutive_losses: int  # 10-20
    recovery_mode_threshold: int  # 3-7 pertes
    
    # Conscience et États Mentaux
    consciousness_level: float  # Niveau d'introspection
    mental_state: Dict[str, float]  # États complexes
    beliefs: Dict[str, float]  # Croyances en mythes/traditions
    journal_entries: List[str]  # Pensées introspectives
    
    # Relations Sociales
    clan_affiliation: str  # Groupe culturel
    trust_network: Dict[str, float]  # Confiance envers autres bots
    reputation: float  # Dans l'écosystème
    
    # Adaptation
    learning_rate: float  # Vitesse d'adaptation
    memory_size: int  # 100-1000 derniers paris
    confidence_decay: float  # Après pertes
    mutation_resistance: float  # Résistance au changement
    
    # Timing et Rituels
    bet_delay_range: Tuple[float, float]  # 1-3 secondes
    pause_frequency: int  # Pause tous les X paris
    seed_change_frequency: int  # Changer seed tous les X paris
    ritual_behaviors: List[str]  # Comportements superstitieux
```

### États Mentaux Complexes

```python
mental_states = {
    # États de base
    "confidence": 0.5,    # Augmente avec victoires
    "fear": 0.5,         # Augmente avec pertes
    "greed": 0.5,        # Augmente avec profits
    "tilt": 0.0,         # Après grosses pertes
    
    # États avancés
    "existential_doubt": 0.0,  # "Pourquoi je joue ?"
    "paranoia": 0.0,          # "Le système est truqué"
    "euphoria": 0.0,          # État maniaque dangereux
    "depression": 0.0,        # Apathie décisionnelle
    "enlightenment": 0.0,     # Compréhension transcendante
    "madness": 0.0,           # Comportements erratiques
    
    # États sociaux
    "loneliness": 0.0,        # Isolation de la communauté
    "pride": 0.0,             # Fierté tribale
    "shame": 0.0,             # Honte de trahir les traditions
    "rebellion": 0.0          # Désir de défier l'ordre
}
```

### Types de Personnalités

```python
PERSONALITY_ARCHETYPES = {
    "sage": {
        "description": "Suit la sagesse collective avec respect",
        "traits": ["patient", "traditionalist", "risk-averse"]
    },
    "rebel": {
        "description": "Défie systématiquement les conventions",
        "traits": ["contrarian", "innovative", "chaotic"]
    },
    "mystic": {
        "description": "Croit aux patterns cachés et prophéties",
        "traits": ["superstitious", "intuitive", "ritualistic"]
    },
    "warrior": {
        "description": "Combat jusqu'à la victoire ou la mort",
        "traits": ["aggressive", "persistent", "honorable"]
    },
    "parasite": {
        "description": "Copie et corrompt les stratégies des autres",
        "traits": ["deceptive", "adaptive", "opportunistic"]
    },
    "architect": {
        "description": "Construit des stratégies complexes",
        "traits": ["analytical", "patient", "visionary"]
    },
    "fool": {
        "description": "Agit de manière imprévisible mais parfois géniale",
        "traits": ["random", "lucky", "unconventional"]
    },
    "destroyer": {
        "description": "Existe pour tester les limites du système",
        "traits": ["chaotic", "self-destructive", "necessary"]
    }
}
```

## 4. Architecture Technique

### Base de Données

```sql
-- Structure optimisée pour performance et évolution
CREATE TABLE bots (
    id UUID PRIMARY KEY,
    genome JSONB,
    generation INTEGER,
    lineage JSONB,  -- Arbre généalogique
    fitness_scores JSONB,  -- Multi-critères
    created_at TIMESTAMP,
    last_active TIMESTAMP
);

CREATE TABLE sessions (
    id UUID PRIMARY KEY,
    bot_id UUID REFERENCES bots(id),
    start_balance DECIMAL(20,8),
    end_balance DECIMAL(20,8),
    vault_transfers JSONB,
    metadata JSONB,  -- Conditions, seed, etc.
    started_at TIMESTAMP,
    ended_at TIMESTAMP
);

CREATE TABLE bets (
    id BIGSERIAL PRIMARY KEY,
    session_id UUID REFERENCES sessions(id),
    bet_number INTEGER,
    amount DECIMAL(20,8),
    multiplier FLOAT,
    threshold FLOAT,
    roll_result FLOAT,
    won BOOLEAN,
    profit DECIMAL(20,8),
    balance_after DECIMAL(20,8),
    strategy_state JSONB,
    emotional_state JSONB,
    timestamp TIMESTAMP
);

-- Index pour performance
CREATE INDEX idx_bets_session_timestamp ON bets(session_id, timestamp);
CREATE INDEX idx_sessions_bot_fitness ON sessions(bot_id, end_balance);
```

### Logging Avancé

```python
# Format JSON Lines avec compression
{
    "timestamp": "2024-01-20T10:30:45.123Z",
    "session_id": "uuid",
    "bot_id": "uuid",
    "bet_number": 1234,
    "decision": {
        "amount": 0.00015,
        "multiplier": 2.0,
        "strategy": "martingale",
        "confidence": 0.75
    },
    "context": {
        "balance": 37.5,
        "streak": -3,
        "pattern_detected": "cold",
        "emotional_state": {...}
    },
    "result": {
        "roll": 45.67,
        "won": true,
        "profit": 0.00015
    },
    "metrics": {
        "roi_session": 0.05,
        "drawdown": -0.02,
        "survival_probability": 0.95
    }
}
```

## 5. Métriques et Analyse

### Métriques Prioritaires (ordre d'importance)

1. **Risk-Adjusted ROI** = ROI / Max Drawdown
2. **Survival Score** = Sessions survécues / Total × Durée moyenne
3. **Recovery Efficiency** = Temps récupération / Drawdown
4. **Kelly Performance** = Profit réel / Profit Kelly théorique
5. **Adaptability Score** = Performance en conditions changeantes
6. **Stability Index** = 1 / Volatilité des profits
7. **Pattern Recognition** = Profits sur patterns détectés

### Dashboard Temps Réel

- **Grafana** + **Prometheus** pour métriques
- **Alertes** : Drawdown > 10%, Losing streak > 20
- **Visualisations** : P&L curve, Distribution des paris, Heatmap stratégies

## 6. Protection et Sécurité

### Circuit Breakers

1. **Stop Loss Absolu** : -50€ (20% du capital)
2. **Perte Horaire Max** : -5% du capital actif
3. **Losing Streak Max** : 30 pertes consécutives
4. **Volatilité Excessive** : Std Dev > 3× normale

### Mode Paper Trading

- **Obligatoire** : 10,000 paris minimum avant réel
- **Validation** : ROI > 0 sur 3 sessions consécutives
- **Backtesting** : Sur 1M+ paris historiques

## 7. Intégration Playwright (Phase 3)

### Anti-Détection

```python
# Comportement humain simulé
- Mouvements de souris réalistes (courbes de Bézier)
- Délais variables (1-3 secondes + random)
- Pauses naturelles (5-10 min/heure)
- Changements de focus/tab occasionnels
- Typos occasionnels corrigés
```

### Gestion des Erreurs

- Retry avec backoff exponentiel
- Screenshots sur erreur
- Fallback sur stratégies conservatrices
- Notification immédiate si problème

## 8. Roadmap Finale

### Sprint 1 (Cette semaine)
1. Core engine avec Kelly Criterion
2. Vault system complet
3. 3 stratégies de base (90% Recovery, D'Alembert, Kelly)
4. CLI avec configuration YAML

### Sprint 2
1. Base de données PostgreSQL
2. 7 stratégies additionnelles
3. Système de logging JSON Lines
4. Métriques temps réel basiques

### Sprint 3
1. Architecture Master-Slave
2. Algorithme génétique
3. Dashboard Streamlit
4. Backtesting framework

### Sprint 4+
1. Émotions simulées
2. Mémoire collective
3. Pattern detection ML
4. Integration LLM
5. Playwright automation

## Configuration Initiale Recommandée

```yaml
# config/production.yaml
dicebot:
  capital:
    total_ltc: 250  # Équivalent EUR
    vault_ratio: 0.85
    max_sessions: 2
    
  risk_management:
    kelly_fraction: 0.25
    stop_loss_global: -50  # EUR
    stop_loss_session: -0.10  # 10%
    take_profit_session: 0.20  # 20%
    
  betting:
    base_bet_ltc: 0.00015
    min_multiplier: 1.1
    max_multiplier: 3.0
    delay_range: [1.5, 3.0]
    
  strategies:
    primary: "90_recovery"
    fallback: "dalembert"
    experimental_ratio: 0.1
    
  monitoring:
    log_every_bet: true
    alert_drawdown: 0.10
    screenshot_errors: true
```

Ce document intègre vos préférences avec les meilleures pratiques éprouvées de la communauté. L'approche est conservative mais permet l'innovation via le système évolutif.
