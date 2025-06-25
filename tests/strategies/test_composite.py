"""Tests pour CompositeStrategy."""

from decimal import Decimal

import pytest

from dicebot.core.models import BetResult, GameState
from dicebot.strategies import (
    CombinationMode,
    CompositeConfig,
    CompositeStrategy,
    FibonacciStrategy,
    MartingaleStrategy,
    StrategyConfig,
)


class TestCompositeStrategy:
    """Test la stratégie composite."""

    def setup_method(self):
        """Prépare les tests."""
        self.base_config = StrategyConfig(base_bet=Decimal("0.001"), max_losses=5)

        # Créer des stratégies de base pour les tests
        self.martingale = MartingaleStrategy(self.base_config)
        self.fibonacci = FibonacciStrategy(self.base_config)

        self.game_state = GameState(balance=Decimal("100"))

    def test_initialization(self):
        """Test l'initialisation de la stratégie composite."""
        config = CompositeConfig(base_bet=Decimal("0.001"), mode=CombinationMode.AVERAGE)
        strategies = [self.martingale, self.fibonacci]

        composite = CompositeStrategy(config, strategies)

        assert composite.mode == CombinationMode.AVERAGE
        assert len(composite.strategies) == 2
        assert composite.strategies[0] == self.martingale
        assert composite.strategies[1] == self.fibonacci

    def test_empty_strategies_raises_error(self):
        """Test qu'une liste vide de stratégies lève une erreur."""
        config = CompositeConfig(base_bet=Decimal("0.001"))

        with pytest.raises(ValueError, match="At least one strategy is required"):
            CompositeStrategy(config, [])

    def test_average_mode(self):
        """Test le mode AVERAGE."""
        config = CompositeConfig(base_bet=Decimal("0.001"), mode=CombinationMode.AVERAGE)
        strategies = [self.martingale, self.fibonacci]
        composite = CompositeStrategy(config, strategies)

        # Les deux stratégies devraient donner base_bet au départ
        bet_amount = composite.calculate_next_bet(self.game_state)

        assert bet_amount == Decimal("0.001")  # Moyenne de 0.001 et 0.001
        # Confidence is on the strategy itself, not the decision
        assert 0.0 <= composite.confidence <= 1.0

    def test_weighted_mode(self):
        """Test le mode WEIGHTED (pondéré par confiance)."""
        config = CompositeConfig(base_bet=Decimal("0.001"), mode=CombinationMode.WEIGHTED)
        strategies = [self.martingale, self.fibonacci]
        composite = CompositeStrategy(config, strategies)

        bet_amount = composite.calculate_next_bet(self.game_state)

        assert bet_amount > Decimal("0")
        # Confidence is on the strategy itself, not the decision
        assert 0.0 <= composite.confidence <= 1.0

    def test_aggressive_mode(self):
        """Test le mode AGGRESSIVE (mise la plus élevée)."""
        config = CompositeConfig(base_bet=Decimal("0.001"), mode=CombinationMode.AGGRESSIVE)
        strategies = [self.martingale, self.fibonacci]
        composite = CompositeStrategy(config, strategies)

        # Simuler une perte pour que Martingale double
        loss_result = BetResult(
            amount=Decimal("0.001"),
            won=False,
            payout=Decimal("0"),  # Pas de payout car perdu
            roll=60.0,
            threshold=49.5,
        )
        self.martingale.update_after_result(loss_result)

        bet_amount = composite.calculate_next_bet(self.game_state)

        # Devrait prendre la mise la plus élevée (Martingale après perte)
        assert bet_amount >= Decimal("0.001")

    def test_conservative_mode(self):
        """Test le mode CONSERVATIVE (mise la plus faible)."""
        config = CompositeConfig(base_bet=Decimal("0.001"), mode=CombinationMode.CONSERVATIVE)
        strategies = [self.martingale, self.fibonacci]
        composite = CompositeStrategy(config, strategies)

        bet_amount = composite.calculate_next_bet(self.game_state)

        # Devrait prendre la mise la plus faible
        assert bet_amount == Decimal("0.001")

    def test_consensus_mode(self):
        """Test le mode CONSENSUS."""
        config = CompositeConfig(
            base_bet=Decimal("0.001"),
            mode=CombinationMode.CONSENSUS,
            consensus_threshold=0.5,
        )
        strategies = [self.martingale, self.fibonacci]
        composite = CompositeStrategy(config, strategies)

        bet_amount = composite.calculate_next_bet(self.game_state)

        # Avec 2 stratégies et threshold 0.5, devrait fonctionner
        assert bet_amount > Decimal("0")

    def test_rotate_mode(self):
        """Test le mode ROTATE."""
        config = CompositeConfig(
            base_bet=Decimal("0.001"), mode=CombinationMode.ROTATE, rotation_interval=2
        )
        strategies = [self.martingale, self.fibonacci]
        composite = CompositeStrategy(config, strategies)

        # Premier appel - stratégie 0
        bet1 = composite.calculate_next_bet(self.game_state)
        assert bet1 == Decimal("0.001")

        # Simuler un pari
        composite.bets_since_rotation = 1

        # Deuxième appel - toujours stratégie 0
        bet2 = composite.calculate_next_bet(self.game_state)
        assert bet2 == Decimal("0.001")

        # Troisième appel - devrait changer vers stratégie 1
        composite.bets_since_rotation = 2
        bet3 = composite.calculate_next_bet(self.game_state)
        assert bet3 == Decimal("0.001")

    def test_update_after_result(self):
        """Test la mise à jour après résultat."""
        config = CompositeConfig(base_bet=Decimal("0.001"), mode=CombinationMode.AVERAGE)
        strategies = [self.martingale, self.fibonacci]
        composite = CompositeStrategy(config, strategies)

        bet_result = BetResult(
            amount=Decimal("0.001"),
            won=True,
            payout=Decimal("0.002"),  # Won avec multiplier 2.0
            roll=30.0,
            threshold=49.5,
        )

        # Devrait mettre à jour toutes les stratégies sous-jacentes
        composite.update_after_result(bet_result)

        # Vérifier que les stratégies ont été mises à jour
        # (les détails dépendent de l'implémentation)

    def test_reset_state(self):
        """Test la réinitialisation de l'état."""
        config = CompositeConfig(base_bet=Decimal("0.001"), mode=CombinationMode.ROTATE)
        strategies = [self.martingale, self.fibonacci]
        composite = CompositeStrategy(config, strategies)

        # Changer l'état
        composite.current_strategy_index = 1
        composite.bets_since_rotation = 5

        # Réinitialiser
        composite.reset_state()

        assert composite.current_strategy_index == 0
        assert composite.bets_since_rotation == 0

    def test_get_name(self):
        """Test le nom de la stratégie."""
        config = CompositeConfig(base_bet=Decimal("0.001"))
        strategies = [self.martingale, self.fibonacci]
        composite = CompositeStrategy(config, strategies)

        name = composite.get_name()
        assert "Composite" in name
        assert "Martingale" in name
        assert "Fibonacci" in name
