from decimal import Decimal

from ..core.models import BetResult, GameState
from .base import BaseStrategy, StrategyConfig


class FlatBetting(BaseStrategy):
    """
    Stratégie Flat Betting : mise constante peu importe le résultat.

    La stratégie la plus simple et la plus conservatrice.
    Utile comme baseline pour comparer avec d'autres stratégies.
    """

    def __init__(self, config: StrategyConfig):
        super().__init__(config)

    def calculate_next_bet(self, game_state: GameState) -> Decimal:
        """Retourne toujours la mise de base"""
        return self.config.base_bet

    def _update_strategy_state(self, result: BetResult) -> None:
        """Aucune mise à jour nécessaire pour flat betting"""
        # La mise reste constante
        pass

    def reset_state(self) -> None:
        """Réinitialise l'état (rien à faire pour flat betting)"""
        self.current_bet = self.config.base_bet
