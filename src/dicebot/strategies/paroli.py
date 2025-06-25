from decimal import Decimal

from ..core.models import BetResult, GameState
from .base import BaseStrategy, StrategyConfig


class ParoliStrategy(BaseStrategy):
    """
    Stratégie Paroli : l'anti-Martingale, double après un gain.

    Règles:
    - Après un gain: doubler la mise (jusqu'à un maximum de gains consécutifs)
    - Après une perte: revenir à la mise de base
    - Après avoir atteint l'objectif de gains consécutifs: revenir à la mise de base

    Plus conservatrice que Martingale car on risque les gains, pas le capital.
    """

    def __init__(self, config: StrategyConfig, target_wins: int = 3):
        super().__init__(config)
        self.target_wins = target_wins  # Nombre de gains consécutifs visés
        self.consecutive_wins = 0
        self.last_bet = config.base_bet

    def calculate_next_bet(self, game_state: GameState) -> Decimal:
        """Calcule la prochaine mise selon la stratégie Paroli"""
        # Si on a atteint l'objectif ou perdu, revenir à la base
        if self.consecutive_wins >= self.target_wins or self.consecutive_wins == 0:
            return self.config.base_bet

        # Sinon, multiplier la dernière mise
        multiplier = Decimal(str(self.config.multiplier))
        next_bet = self.last_bet * multiplier

        return next_bet

    def _update_strategy_state(self, result: BetResult) -> None:
        """Met à jour l'état après un résultat"""
        if result.won:
            self.consecutive_wins += 1
            # Si on atteint l'objectif, on reset au prochain tour
            if self.consecutive_wins >= self.target_wins:
                self.current_bet = self.config.base_bet
            else:
                # Continuer la progression
                self.current_bet = result.amount * Decimal(str(self.config.multiplier))
        else:
            # Reset après une perte
            self.consecutive_wins = 0
            self.current_bet = self.config.base_bet

        self.last_bet = result.amount

    def reset_state(self) -> None:
        """Réinitialise l'état de la stratégie"""
        self.consecutive_wins = 0
        self.current_bet = self.config.base_bet
        self.last_bet = self.config.base_bet

    def get_consecutive_wins(self) -> int:
        """Retourne le nombre de gains consécutifs actuels"""
        return self.consecutive_wins

    def get_target_wins(self) -> int:
        """Retourne l'objectif de gains consécutifs"""
        return self.target_wins
