from decimal import Decimal

from ..core.models import BetResult, GameState
from .base import BaseStrategy, StrategyConfig


class FibonacciStrategy(BaseStrategy):
    """
    Stratégie Fibonacci : suit la séquence de Fibonacci pour les mises.

    Règles:
    - Après une perte: avancer d'un niveau dans la séquence
    - Après un gain: reculer de deux niveaux
    - La mise = base_bet * nombre de Fibonacci actuel

    Plus conservatrice que Martingale car la progression est plus lente.
    """

    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        # Séquence de Fibonacci pré-calculée
        self.sequence = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610]
        self.current_index = 0
        # Limiter la séquence selon max_losses
        if config.max_losses < len(self.sequence):
            self.sequence = self.sequence[: config.max_losses]

    def calculate_next_bet(self, game_state: GameState) -> Decimal:
        """Calcule la prochaine mise selon la séquence de Fibonacci"""
        # Obtenir le multiplicateur de la séquence
        fib_multiplier = self.sequence[self.current_index]

        # Calculer la mise
        next_bet = self.config.base_bet * Decimal(str(fib_multiplier))

        return next_bet

    def _update_strategy_state(self, result: BetResult) -> None:
        """Met à jour la position dans la séquence après un résultat"""
        if result.won:
            # Reculer de 2 positions (ou revenir au début)
            self.current_index = max(0, self.current_index - 2)
        else:
            # Avancer d'une position (sans dépasser la fin)
            self.current_index = min(len(self.sequence) - 1, self.current_index + 1)

        # Mettre à jour la mise courante pour info
        fib_multiplier = self.sequence[self.current_index]
        self.current_bet = self.config.base_bet * Decimal(str(fib_multiplier))

    def reset_state(self) -> None:
        """Réinitialise l'état de la stratégie"""
        self.current_index = 0
        self.current_bet = self.config.base_bet

    def get_current_level(self) -> int:
        """Retourne le niveau actuel dans la séquence (pour debug/info)"""
        return self.current_index

    def get_sequence_value(self) -> int:
        """Retourne la valeur actuelle de la séquence"""
        return self.sequence[self.current_index]
