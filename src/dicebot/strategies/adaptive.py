"""Stratégie adaptative qui change dynamiquement selon les conditions."""

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum, auto
from typing import Any

from ..core.models import BetResult, GameState
from .base import BaseStrategy, StrategyConfig


class SwitchCondition(Enum):
    """Conditions pour changer de stratégie."""

    CONSECUTIVE_LOSSES = auto()
    CONSECUTIVE_WINS = auto()
    DRAWDOWN_THRESHOLD = auto()
    PROFIT_TARGET = auto()
    LOW_CONFIDENCE = auto()
    TIME_BASED = auto()
    BALANCE_THRESHOLD = auto()


@dataclass
class StrategyRule:
    """Règle pour changer de stratégie."""

    condition: SwitchCondition
    threshold: float
    target_strategy: str
    target_config: dict[str, Any] = field(default_factory=dict)
    cooldown_bets: int = 10  # Nombre de paris avant de pouvoir re-switcher


@dataclass
class AdaptiveConfig(StrategyConfig):
    """Configuration pour la stratégie adaptative."""

    initial_strategy: str = "flat"
    initial_config: dict[str, Any] = field(default_factory=dict)
    rules: list[StrategyRule] = field(default_factory=list)
    min_bets_before_switch: int = 5  # Minimum de paris avant de pouvoir changer


class AdaptiveStrategy(BaseStrategy):
    """
    Stratégie qui change dynamiquement selon les conditions du marché.

    Permet de s'adapter automatiquement aux différentes phases du jeu:
    - Conservative en période de pertes
    - Aggressive en période de gains
    - Changement selon le drawdown, la confiance, etc.
    """

    def __init__(self, config: AdaptiveConfig):
        # Initialize adaptive-specific attributes BEFORE calling super().__init__
        # because BaseStrategy.__init__ calls reset_state() which needs these attributes
        self.adaptive_config = config
        self.initial_strategy = config.initial_strategy
        self.rules = config.rules

        # Initialize attributes that reset_state() will use
        self.current_strategy = None
        self.current_strategy_name = config.initial_strategy
        self.switch_history: list[tuple[int, str, str, str]] = []
        self.bets_since_switch = 0
        self.bets_in_current_strategy = 0  # For test compatibility
        self.last_switch_bet = 0  # For test compatibility
        self.cooldown_counters: dict[str, int] = {}
        self.initial_balance: Decimal | None = None
        self.peak_balance: Decimal | None = None

        # Now call parent constructor
        super().__init__(config)

        # Create the initial strategy after parent initialization
        # (import différé pour éviter les imports circulaires)
        from .factory import StrategyFactory

        self.current_strategy = StrategyFactory.create_from_dict(
            {
                "strategy": config.initial_strategy,
                "base_bet": str(config.base_bet),  # Convert Decimal to string for factory
                **config.initial_config,
            }
        )

    def calculate_next_bet(self, game_state: GameState) -> Decimal:
        """Calcule la prochaine mise avec la stratégie courante."""
        # Initialiser les balances si nécessaire
        if self.initial_balance is None:
            self.initial_balance = game_state.balance
            self.peak_balance = game_state.balance

        # Vérifier si on doit changer de stratégie
        self._check_switch_conditions(game_state)

        # Utiliser la stratégie courante
        return self.current_strategy.calculate_next_bet(game_state)

    def _update_strategy_state(self, result: BetResult) -> None:
        """Met à jour l'état de la stratégie courante."""
        self.current_strategy.update_after_result(result)
        self.bets_since_switch += 1
        self.bets_in_current_strategy += 1  # For test compatibility

        # Décrémenter les cooldowns
        for strategy in list(self.cooldown_counters.keys()):
            self.cooldown_counters[strategy] -= 1
            if self.cooldown_counters[strategy] <= 0:
                del self.cooldown_counters[strategy]

    def reset_state(self) -> None:
        """Réinitialise l'état."""
        if self.current_strategy is not None:
            self.current_strategy.reset_state()

        # Reset strategy to initial
        self.current_strategy_name = self.initial_strategy

        # Reset counters and history
        self.switch_history.clear()
        self.bets_since_switch = 0
        self.bets_in_current_strategy = 0  # For test compatibility
        self.last_switch_bet = 0  # For test compatibility
        self.cooldown_counters.clear()

        # Reset balance tracking
        self.initial_balance = None
        self.peak_balance = None
        self.confidence = 1.0

    def _check_switch_conditions(self, game_state: GameState) -> None:
        """Vérifie si on doit changer de stratégie."""
        # Mise à jour du peak balance
        if self.peak_balance is not None:
            self.peak_balance = max(self.peak_balance, game_state.balance)

        # Ne pas changer trop tôt
        if self.bets_since_switch < self.adaptive_config.min_bets_before_switch:
            return

        # Vérifier chaque règle
        for rule in self.adaptive_config.rules:
            if self._should_switch(rule, game_state):
                self._switch_strategy(rule, game_state)
                break

    def _should_switch(self, rule: StrategyRule, game_state: GameState) -> bool:
        """Vérifie si une règle de switch est satisfaite."""
        # Vérifier le cooldown
        if rule.target_strategy in self.cooldown_counters:
            return False

        # Vérifier la condition
        if rule.condition == SwitchCondition.CONSECUTIVE_LOSSES:
            return game_state.consecutive_losses >= rule.threshold

        elif rule.condition == SwitchCondition.CONSECUTIVE_WINS:
            return game_state.consecutive_wins >= rule.threshold

        elif rule.condition == SwitchCondition.DRAWDOWN_THRESHOLD:
            if self.peak_balance is None:
                return False
            current_drawdown = float((self.peak_balance - game_state.balance) / self.peak_balance)
            return current_drawdown >= rule.threshold

        elif rule.condition == SwitchCondition.PROFIT_TARGET:
            if self.initial_balance is None:
                return False
            roi = float((game_state.balance - self.initial_balance) / self.initial_balance)
            return roi >= rule.threshold

        elif rule.condition == SwitchCondition.LOW_CONFIDENCE:
            return self.current_strategy.confidence <= rule.threshold

        elif rule.condition == SwitchCondition.BALANCE_THRESHOLD:
            if self.initial_balance is None:
                return False
            balance_ratio = float(game_state.balance / self.initial_balance)
            return balance_ratio <= rule.threshold

        return False

    def _switch_strategy(self, rule: StrategyRule, game_state: GameState) -> None:
        """Change de stratégie."""
        old_strategy = self.current_strategy_name

        # Créer la nouvelle stratégie (import différé)
        from .factory import StrategyFactory

        new_config = {
            "strategy": rule.target_strategy,
            **rule.target_config,
            "base_bet": str(self.config.base_bet),  # Convert Decimal to string for factory
        }

        try:
            self.current_strategy = StrategyFactory.create_from_dict(new_config)
            self.current_strategy_name = rule.target_strategy

            # Enregistrer le changement
            self.switch_history.append(
                (
                    game_state.bets_count,
                    old_strategy,
                    rule.target_strategy,
                    rule.condition.name,
                )
            )

            # Reset les compteurs
            self.bets_since_switch = 0
            self.bets_in_current_strategy = 0  # For test compatibility
            self.last_switch_bet = game_state.bets_count  # For test compatibility
            self.cooldown_counters[old_strategy] = rule.cooldown_bets

            # Transférer la confiance (avec bonus pour le changement)
            self.current_strategy.confidence = min(1.0, self.confidence * 1.1)

        except Exception as e:
            # En cas d'erreur, garder la stratégie actuelle
            print(f"Error switching strategy: {e}")

    def get_name(self) -> str:
        """Retourne le nom de la stratégie adaptative."""
        return f"Adaptive[{self.current_strategy_name}]"

    def get_switch_history(self) -> list[tuple[int, str, str, str]]:
        """Retourne l'historique des changements de stratégie."""
        return self.switch_history.copy()

    def on_winning_streak(self, streak_length: int, game_state: GameState) -> None:
        """Propage l'événement à la stratégie courante."""
        self.current_strategy.on_winning_streak(streak_length, game_state)

    def on_losing_streak(self, streak_length: int, game_state: GameState) -> None:
        """Propage l'événement à la stratégie courante."""
        self.current_strategy.on_losing_streak(streak_length, game_state)
