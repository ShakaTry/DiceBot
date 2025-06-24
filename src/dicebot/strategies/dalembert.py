from decimal import Decimal

from ..core.models import BetResult, GameState
from .base import BaseStrategy, StrategyConfig


class DAlembert(BaseStrategy):
    """
    Stratégie D'Alembert : progression arithmétique des mises.

    Règles:
    - Après une perte: augmenter la mise d'une unité
    - Après un gain: diminuer la mise d'une unité
    - Ne jamais descendre en dessous de la mise de base

    Plus conservatrice que Martingale car la progression est linéaire,
    pas exponentielle.
    """

    def __init__(self, config: StrategyConfig):
        self.current_units = 1
        self.unit_value = config.base_bet
        # Limite maximale d'unités basée sur max_losses
        self.max_units = config.max_losses
        super().__init__(config)

    def calculate_next_bet(self, game_state: GameState) -> Decimal:
        """Calcule la prochaine mise selon D'Alembert"""
        return self.unit_value * Decimal(str(self.current_units))

    def _update_strategy_state(self, result: BetResult) -> None:
        """Met à jour le nombre d'unités après un résultat"""
        if result.won:
            # Diminuer d'une unité (minimum 1)
            self.current_units = max(1, self.current_units - 1)
        else:
            # Augmenter d'une unité (avec limite max)
            self.current_units = min(self.max_units, self.current_units + 1)

        # Mettre à jour la mise courante
        self.current_bet = self.unit_value * Decimal(str(self.current_units))

    def reset_state(self) -> None:
        """Réinitialise l'état de la stratégie"""
        self.current_units = 1
        self.current_bet = self.unit_value

    def get_current_units(self) -> int:
        """Retourne le nombre d'unités actuel (pour debug/info)"""
        return self.current_units
