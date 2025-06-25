from decimal import Decimal

from ..core.models import BetResult, GameState
from .base import BaseStrategy, StrategyConfig


class MartingaleStrategy(BaseStrategy):
    """
    Stratégie Martingale : double la mise après chaque perte,
    reset à la mise de base après un gain.

    Risques:
    - Peut atteindre rapidement les limites de table
    - Nécessite un bankroll important
    - Les séries de pertes peuvent être dévastatrices
    """

    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.consecutive_losses = 0
        self.last_bet = config.base_bet

    def calculate_next_bet(self, game_state: GameState) -> Decimal:
        """Calcule la prochaine mise selon la stratégie Martingale"""
        # Protection contre trop de pertes consécutives
        if self.consecutive_losses >= self.config.max_losses:
            # Reset à la mise de base pour éviter la ruine
            return self.config.base_bet

        # Si la dernière mise était perdante, on double
        if self.consecutive_losses > 0:
            multiplier = Decimal(str(self.config.multiplier)) ** self.consecutive_losses
            next_bet = self.config.base_bet * multiplier
        else:
            # Sinon, mise de base
            next_bet = self.config.base_bet

        return next_bet

    def _update_strategy_state(self, result: BetResult) -> None:
        """Met à jour l'état spécifique à la stratégie Martingale"""
        if result.won:
            # Reset après un gain
            self.consecutive_losses = 0
            self.current_bet = self.config.base_bet
        else:
            # Incrémenter les pertes consécutives
            self.consecutive_losses += 1
            # La prochaine mise sera calculée dans calculate_next_bet

        self.last_bet = result.amount

    def reset_state(self) -> None:
        """Réinitialise l'état de la stratégie"""
        self.consecutive_losses = 0
        self.current_bet = self.config.base_bet
        self.last_bet = self.config.base_bet
