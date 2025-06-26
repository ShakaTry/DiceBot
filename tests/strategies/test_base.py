from decimal import Decimal

import pytest

from dicebot.core.models import BetResult, GameState
from dicebot.strategies.base import BaseStrategy, StrategyConfig


class ConcreteStrategy(BaseStrategy):
    """Implémentation concrète pour les tests"""

    def calculate_next_bet(self, game_state: GameState) -> Decimal:
        return self.config.base_bet

    def _update_strategy_state(self, result: BetResult) -> None:
        pass

    def reset_state(self) -> None:
        pass


class TestBaseStrategy:
    def test_cannot_instantiate_abstract_class(self) -> None:
        """Vérifie que la classe abstraite ne peut pas être instanciée"""
        config: StrategyConfig = StrategyConfig(base_bet=Decimal("1"))
        with pytest.raises(TypeError):
            BaseStrategy(config)  # type: ignore[abstract]

    def test_bet_limits_respected(self) -> None:
        """Vérifie que les limites min/max sont respectées"""
        config: StrategyConfig = StrategyConfig(
            base_bet=Decimal("1"), min_bet=Decimal("0.1"), max_bet=Decimal("10")
        )
        strategy: ConcreteStrategy = ConcreteStrategy(config)

        # Test avec limite max
        bet: Decimal = strategy._apply_limits(Decimal("20"), Decimal("100"))  # type: ignore[misc]
        assert bet == Decimal("10")

        # Test avec limite min
        bet = strategy._apply_limits(Decimal("0.01"), Decimal("100"))  # type: ignore[misc]
        assert bet == Decimal("0.1")

        # Test avec limite du bankroll
        bet = strategy._apply_limits(Decimal("5"), Decimal("3"))  # type: ignore[misc]
        assert bet == Decimal("3")

    def test_insufficient_balance(self) -> None:
        """Vérifie le comportement avec balance insuffisante"""
        config: StrategyConfig = StrategyConfig(base_bet=Decimal("1"), min_bet=Decimal("1"))
        strategy: ConcreteStrategy = ConcreteStrategy(config)

        game_state: GameState = GameState(balance=Decimal("0.5"))
        decision = strategy.decide_bet(game_state)

        assert decision.skip is True
        assert decision.reason == "Insufficient balance"
        assert decision.amount == Decimal("0")

    def test_bet_below_minimum_after_limits(self) -> None:
        """Vérifie le comportement quand la mise devient trop petite après limites"""
        config: StrategyConfig = StrategyConfig(base_bet=Decimal("10"), min_bet=Decimal("5"))
        strategy: ConcreteStrategy = ConcreteStrategy(config)

        # Balance de 3, donc insuffisant pour la mise minimum de 5
        game_state: GameState = GameState(balance=Decimal("3"))
        decision = strategy.decide_bet(game_state)

        assert decision.skip is True
        assert decision.reason == "Insufficient balance"

    def test_valid_bet_decision(self) -> None:
        """Vérifie qu'une décision valide est prise dans des conditions normales"""
        config: StrategyConfig = StrategyConfig(base_bet=Decimal("1"), default_multiplier=2.5)
        strategy: ConcreteStrategy = ConcreteStrategy(config)

        game_state: GameState = GameState(balance=Decimal("100"))
        decision = strategy.decide_bet(game_state)

        assert decision.skip is False
        assert decision.amount == Decimal("1")
        # Le multiplicateur est maintenant calculé depuis target/bet_type
        assert 1.8 <= decision.multiplier <= 2.5  # Tolérance pour le calcul automatique
        assert decision.bet_type is not None
        assert decision.target > 0
        assert decision.reason is None

    def test_get_name(self) -> None:
        """Vérifie que le nom de la stratégie est correctement extrait"""
        config: StrategyConfig = StrategyConfig(base_bet=Decimal("1"))
        strategy: ConcreteStrategy = ConcreteStrategy(config)

        assert strategy.get_name() == "Concrete"
