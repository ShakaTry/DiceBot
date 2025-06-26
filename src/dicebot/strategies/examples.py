"""Exemples d'utilisation des stratégies améliorées."""

from decimal import Decimal

from ..core.models import GameState
from .adaptive import AdaptiveConfig, AdaptiveStrategy, StrategyRule, SwitchCondition
from .composite import CompositeStrategy
from .factory import StrategyFactory


def create_conservative_adaptive_strategy() -> AdaptiveStrategy:
    """
    Crée une stratégie adaptative conservative.

    - Commence avec flat betting
    - Passe à D'Alembert après 3 gains consécutifs
    - Revient à flat après 5 pertes consécutives
    - Passe à Fibonacci si drawdown > 20%
    """
    config = AdaptiveConfig(
        base_bet=Decimal("0.00015"),
        initial_strategy="flat",
        initial_config={},
        rules=[
            # Après 3 gains, devenir un peu plus agressif
            StrategyRule(
                condition=SwitchCondition.CONSECUTIVE_WINS,
                threshold=3,
                target_strategy="dalembert",
                target_config={"max_losses": 10},
                cooldown_bets=20,
            ),
            # Après 5 pertes, revenir au flat betting
            StrategyRule(
                condition=SwitchCondition.CONSECUTIVE_LOSSES,
                threshold=5,
                target_strategy="flat",
                target_config={},
                cooldown_bets=10,
            ),
            # Si drawdown > 20%, passer à Fibonacci (plus conservateur)
            StrategyRule(
                condition=SwitchCondition.DRAWDOWN_THRESHOLD,
                threshold=0.2,
                target_strategy="fibonacci",
                target_config={"max_losses": 8},
                cooldown_bets=30,
            ),
            # Si profit > 50%, passer à Paroli pour maximiser
            StrategyRule(
                condition=SwitchCondition.PROFIT_TARGET,
                threshold=0.5,
                target_strategy="paroli",
                target_config={"target_wins": 3},
                cooldown_bets=20,
            ),
        ],
        min_bets_before_switch=10,
    )

    return AdaptiveStrategy(config)


def create_aggressive_composite_strategy() -> CompositeStrategy:
    """
    Crée une stratégie composite agressive.

    Combine Martingale, Paroli et Fibonacci en mode agressif
    (prend toujours la mise la plus élevée).
    """
    return StrategyFactory.create_composite(
        strategies=[
            ("martingale", {"base_bet": "0.00015", "max_losses": 5, "multiplier": 2.0}),
            ("paroli", {"base_bet": "0.00015", "target_wins": 4}),
            ("fibonacci", {"base_bet": "0.00015", "max_losses": 10}),
        ],
        mode="aggressive",
        base_config={"base_bet": Decimal("0.00015")},
    )


def create_balanced_composite_strategy() -> CompositeStrategy:
    """
    Crée une stratégie composite équilibrée.

    Utilise la moyenne pondérée par confiance de plusieurs stratégies.
    """
    return StrategyFactory.create_composite(
        strategies=[
            ("martingale", {"base_bet": "0.00015", "max_losses": 8}),
            ("dalembert", {"base_bet": "0.00015", "max_losses": 15}),
            ("flat", {"base_bet": "0.00015"}),
        ],
        mode="weighted",
        base_config={"base_bet": Decimal("0.00015"), "max_bet": Decimal("0.1")},
    )


def create_consensus_composite_strategy() -> CompositeStrategy:
    """
    Crée une stratégie composite basée sur le consensus.

    Ne mise que si au moins 60% des stratégies sont d'accord.
    """
    return StrategyFactory.create_composite(
        strategies=[
            ("martingale", {"base_bet": "0.00015", "max_losses": 5}),
            ("fibonacci", {"base_bet": "0.00015", "max_losses": 8}),
            ("dalembert", {"base_bet": "0.00015", "max_losses": 10}),
            ("flat", {"base_bet": "0.00015"}),
            ("paroli", {"base_bet": "0.00015", "target_wins": 3}),
        ],
        mode="consensus",
        base_config={"base_bet": Decimal("0.00015"), "consensus_threshold": 0.6},
    )


def create_rotating_composite_strategy() -> CompositeStrategy:
    """
    Crée une stratégie composite qui alterne entre stratégies.

    Change de stratégie tous les 20 paris.
    """
    return StrategyFactory.create_composite(
        strategies=[
            ("martingale", {"base_bet": "0.00015", "max_losses": 7}),
            ("fibonacci", {"base_bet": "0.00015", "max_losses": 10}),
            ("dalembert", {"base_bet": "0.00015", "max_losses": 12}),
            ("paroli", {"base_bet": "0.00015", "target_wins": 3}),
        ],
        mode="rotate",
        base_config={"base_bet": Decimal("0.00015"), "rotation_interval": 20},
    )


# Exemples d'utilisation avec le système d'événements
def create_event_aware_strategy():
    """
    Crée une stratégie qui réagit aux événements.
    """
    from .base import StrategyConfig
    from .martingale import MartingaleStrategy

    class EventAwareMartingale(MartingaleStrategy):
        """Martingale qui ajuste son comportement selon les événements."""

        def on_winning_streak(self, streak_length: int, game_state: GameState) -> None:
            """Réduit l'agressivité après une série de gains."""
            if streak_length >= 5:
                # Réduire temporairement le multiplier
                self.config.multiplier = 1.5
                self.confidence *= 0.9

        def on_losing_streak(self, streak_length: int, game_state: GameState) -> None:
            """Devient plus conservateur après trop de pertes."""
            if streak_length >= 7:
                # Forcer un reset
                self.consecutive_losses = 0
                self.current_bet = self.config.base_bet
                self.confidence *= 0.7

    config = StrategyConfig(base_bet=Decimal("0.00015"), max_losses=10, multiplier=2.0)

    return EventAwareMartingale(config)


# Configuration pour différents profils de risque
RISK_PROFILES = {
    "conservative": {
        "strategies": ["flat", "dalembert", "fibonacci"],
        "max_losses": 15,
        "base_bet_ratio": 0.001,  # 0.1% du bankroll
        "stop_loss": 0.1,  # 10%
        "take_profit": 0.2,  # 20%
    },
    "moderate": {
        "strategies": ["fibonacci", "dalembert", "martingale"],
        "max_losses": 10,
        "base_bet_ratio": 0.002,  # 0.2% du bankroll
        "stop_loss": 0.15,  # 15%
        "take_profit": 0.3,  # 30%
    },
    "aggressive": {
        "strategies": ["martingale", "paroli"],
        "max_losses": 7,
        "base_bet_ratio": 0.005,  # 0.5% du bankroll
        "stop_loss": 0.25,  # 25%
        "take_profit": 0.5,  # 50%
    },
    "ultra_aggressive": {
        "strategies": ["martingale", "paroli"],
        "max_losses": 5,
        "base_bet_ratio": 0.01,  # 1% du bankroll
        "stop_loss": 0.5,  # 50%
        "take_profit": 1.0,  # 100%
    },
}
