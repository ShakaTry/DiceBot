# Décisions de Design - DiceBot

## Principe Directeur : Évolutivité

Le simulateur doit être conçu dès le départ pour supporter l'ajout ultérieur du système évolutif Master-Slave.

## 1. Architecture du Simulateur

### Design Pattern : Strategy + Observer

```python
# Permettre l'ajout facile de nouvelles stratégies
class BaseStrategy(ABC):
    @abstractmethod
    def decide_bet(self, game_state: GameState) -> BetDecision:
        pass
    
    @abstractmethod
    def update_state(self, result: BetResult) -> None:
        pass
    
    @abstractmethod
    def get_genome(self) -> Dict[str, Any]:
        """Pour compatibilité future avec système évolutif"""
        pass

# Observer pour collecter les données
class DataCollector:
    def on_bet_placed(self, bet: Bet) -> None
    def on_bet_resolved(self, result: BetResult) -> None
    def on_session_end(self, stats: SessionStats) -> None
```

### Structure Modulaire

```
dicebot/
├── core/
│   ├── game_engine.py      # Logique pure du jeu
│   ├── house_edge.py       # Gestion du 1% edge
│   └── random_engine.py    # RNG avec seed contrôlé
├── money/
│   ├── vault.py           # Gestion vault/bankroll
│   ├── session_manager.py # Gestion des sessions
│   └── risk_manager.py    # Stop-loss, take-profit
├── strategies/
│   ├── base.py           # Interface commune
│   ├── classic/          # Stratégies traditionnelles
│   └── evolved/          # Future: stratégies évoluées
├── simulation/
│   ├── runner.py         # Orchestrateur
│   ├── parallel_runner.py # Future: multi-bot
│   └── config.py         # Configuration centralisée
└── analysis/
    ├── metrics.py        # Calculs de performance
    ├── logger.py         # Système de log détaillé
    └── visualizer.py     # Graphiques et rapports
```

## 2. Gestion des Données

### Format Unifié pour l'Évolution

```python
@dataclass
class BetRecord:
    # Identifiants
    session_id: str
    bot_id: str  # "manual" pour phase 1, UUID pour évolution
    timestamp: float
    
    # Décision
    bet_amount: Decimal
    multiplier: float
    threshold: float
    
    # Contexte
    bankroll_before: Decimal
    current_streak: int
    strategy_state: Dict[str, Any]
    
    # Résultat
    roll_result: float
    won: bool
    profit: Decimal
    bankroll_after: Decimal
    
    # Métadonnées évolutives
    genome_version: Optional[str] = None
    generation: Optional[int] = None
```

### Base de Données Extensible

```sql
-- Tables préparées pour l'évolution
CREATE TABLE bots (
    id TEXT PRIMARY KEY,
    genome JSON,
    generation INTEGER DEFAULT 0,
    parent_ids JSON,
    created_at TIMESTAMP
);

CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    bot_id TEXT REFERENCES bots(id),
    vault_balance DECIMAL,
    bankroll_start DECIMAL,
    bankroll_end DECIMAL,
    started_at TIMESTAMP,
    ended_at TIMESTAMP
);

CREATE TABLE bets (
    -- Tous les champs de BetRecord
);
```

## 3. Configuration Flexible

### YAML pour Paramètres

```yaml
# config/simulator.yaml
game:
  house_edge: 0.01
  min_bet: 0.00000001  # En LTC
  max_bet: 1000
  
vault:
  enabled: true
  vault_ratio: 0.8
  auto_rebalance: true
  rebalance_threshold: 0.5
  
session:
  default_bankroll_ratio: 0.2
  stop_loss: -0.5  # -50% de la bankroll session
  take_profit: 1.0  # +100% de la bankroll session
  max_bets: 10000
  
strategies:
  available:
    - martingale
    - fibonacci
    - dalembert
    - custom
  
logging:
  level: INFO
  detailed_bets: true
  file_format: jsonl
  rotation: daily
```

## 4. Interfaces Préparées

### Pour le Futur Master

```python
class StrategyInterface(Protocol):
    """Interface que devront implémenter les bots évolués"""
    
    def get_genome(self) -> Genome
    def set_genome(self, genome: Genome) -> None
    def mutate(self, rate: float) -> None
    def crossover(self, other: 'StrategyInterface') -> 'StrategyInterface'
    def get_fitness_score(self) -> float
```

### Pour l'IA

```python
class AIAdvisor(Protocol):
    """Interface pour intégration LLM future"""
    
    def analyze_session(self, history: List[BetRecord]) -> Analysis
    def suggest_adjustment(self, current_state: GameState) -> Suggestion
    def generate_strategy(self, constraints: Dict) -> Strategy
```

## 5. Métriques Extensibles

### Système de Scoring Multi-Critères

```python
class MetricsCalculator:
    def calculate_basic_metrics(self, session: Session) -> BasicMetrics:
        """ROI, win_rate, etc."""
        
    def calculate_risk_metrics(self, session: Session) -> RiskMetrics:
        """Drawdown, volatility, etc."""
        
    def calculate_evolution_metrics(self, session: Session) -> EvolutionMetrics:
        """Pour futur: fitness, adaptability, etc."""
```

## 6. Décisions Techniques Clés

### 1. Decimal vs Float
- **Décision** : Utiliser `Decimal` pour tout ce qui touche à l'argent
- **Raison** : Précision critique pour les petites mises en crypto

### 2. Async vs Sync
- **Décision** : Core synchrone, runners async
- **Raison** : Simplicité pour le core, performance pour les simulations batch

### 3. Stockage
- **Décision** : SQLite pour dev, PostgreSQL pour production
- **Raison** : Migration facile, pas de dépendances pour commencer

### 4. Logs
- **Décision** : JSON Lines (.jsonl) pour les logs détaillés
- **Raison** : Facile à parser, streamer, et analyser

## 7. Points d'Extension

### Hooks pour l'Évolution

```python
class GameEngine:
    def __init__(self):
        self.pre_bet_hooks = []
        self.post_bet_hooks = []
        self.session_hooks = []
    
    def add_hook(self, event: str, callback: Callable) -> None:
        """Permet d'ajouter des comportements sans modifier le core"""
```

### Factory Pattern pour Stratégies

```python
class StrategyFactory:
    _strategies = {}
    
    @classmethod
    def register(cls, name: str, strategy_class: Type[BaseStrategy]):
        cls._strategies[name] = strategy_class
    
    @classmethod
    def create(cls, name: str, **params) -> BaseStrategy:
        return cls._strategies[name](**params)
```

## 8. Performance et Scalabilité

### Optimisations Prévues
1. **Cache** : Résultats de calculs coûteux
2. **Batch Processing** : Pour simulations multiples
3. **Multiprocessing** : Pour bots parallèles (phase 2)
4. **Profiling** : Points de mesure intégrés

### Limites Connues
1. **Mémoire** : Max ~1M de paris en RAM
2. **CPU** : Single-thread pour phase 1
3. **I/O** : Logs peuvent ralentir si trop détaillés

## Questions Ouvertes

1. **Reproductibilité** : Seeds fixes ou aléatoires pour les tests ?
2. **Déterminisme** : Important pour comparer les stratégies ?
3. **Temps réel** : Simuler les délais entre paris ou vitesse max ?
