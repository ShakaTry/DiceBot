from decimal import Decimal

from dicebot.core.models import BetResult, GameState
from dicebot.strategies.base import StrategyConfig
from dicebot.strategies.flat import FlatBetting


class TestFlatBetting:
    def test_constant_bet(self) -> None:
        """Vérifie que la mise reste constante"""
        config = StrategyConfig(base_bet=Decimal("1.5"))
        strategy = FlatBetting(config)
        game_state = GameState(balance=Decimal("100"))

        # Première mise
        assert strategy.calculate_next_bet(game_state) == Decimal("1.5")

        # Après une perte
        result = BetResult(
            roll=60.0,
            won=False,
            threshold=49.5,
            amount=Decimal("1.5"),
            payout=Decimal("0"),
        )
        strategy.update_after_result(result)
        assert strategy.calculate_next_bet(game_state) == Decimal("1.5")

        # Après un gain
        result = BetResult(
            roll=40.0,
            won=True,
            threshold=49.5,
            amount=Decimal("1.5"),
            payout=Decimal("3.0"),
        )
        strategy.update_after_result(result)
        assert strategy.calculate_next_bet(game_state) == Decimal("1.5")

    def test_reset_state(self) -> None:
        """Vérifie que reset_state fonctionne"""
        config = StrategyConfig(base_bet=Decimal("2"))
        strategy = FlatBetting(config)

        strategy.current_bet = Decimal("5")  # Modifier artificiellement
        strategy.reset_state()

        assert strategy.current_bet == Decimal("2")
