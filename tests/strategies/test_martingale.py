from decimal import Decimal

from dicebot.core.models import BetResult, GameState
from dicebot.strategies.base import StrategyConfig
from dicebot.strategies.martingale import MartingaleStrategy


class TestMartingaleStrategy:
    def test_initialization(self) -> None:
        """Test l'initialisation de la stratégie"""
        config = StrategyConfig(base_bet=Decimal("1"))
        strategy = MartingaleStrategy(config)

        assert strategy.consecutive_losses == 0
        assert strategy.current_bet == Decimal("1")
        assert strategy.last_bet == Decimal("1")

    def test_double_after_loss(self) -> None:
        """Vérifie que la mise double après une perte"""
        config = StrategyConfig(base_bet=Decimal("1"), multiplier=2.0)
        strategy = MartingaleStrategy(config)
        game_state = GameState(balance=Decimal("100"))

        # Simuler une perte
        result = BetResult(
            roll=60.0,
            won=False,
            threshold=49.5,
            amount=Decimal("1"),
            payout=Decimal("0"),
        )
        strategy.update_after_result(result)

        # La prochaine mise devrait être doublée
        next_bet = strategy.calculate_next_bet(game_state)
        assert next_bet == Decimal("2")

    def test_reset_after_win(self) -> None:
        """Vérifie que la mise revient à la base après un gain"""
        config = StrategyConfig(base_bet=Decimal("1"))
        strategy = MartingaleStrategy(config)
        game_state = GameState(balance=Decimal("100"))

        # Simuler quelques pertes
        for _ in range(3):
            result = BetResult(
                roll=60.0,
                won=False,
                threshold=49.5,
                amount=Decimal("1"),
                payout=Decimal("0"),
            )
            strategy.update_after_result(result)

        assert strategy.consecutive_losses == 3

        # Simuler un gain
        result = BetResult(
            roll=40.0,
            won=True,
            threshold=49.5,
            amount=Decimal("8"),
            payout=Decimal("16"),
        )
        strategy.update_after_result(result)

        # Devrait être reset
        assert strategy.consecutive_losses == 0
        next_bet = strategy.calculate_next_bet(game_state)
        assert next_bet == Decimal("1")

    def test_max_losses_protection(self) -> None:
        """Vérifie la protection contre trop de pertes consécutives"""
        config = StrategyConfig(base_bet=Decimal("1"), max_losses=5)
        strategy = MartingaleStrategy(config)
        game_state = GameState(balance=Decimal("1000"))

        # Simuler max_losses pertes
        for _ in range(5):
            result = BetResult(
                roll=60.0,
                won=False,
                threshold=49.5,
                amount=Decimal("1"),
                payout=Decimal("0"),
            )
            strategy.update_after_result(result)

        # La mise devrait revenir à la base
        next_bet = strategy.calculate_next_bet(game_state)
        assert next_bet == Decimal("1")

    def test_exponential_progression(self) -> None:
        """Vérifie la progression exponentielle des mises"""
        config = StrategyConfig(base_bet=Decimal("1"), multiplier=2.0, max_losses=10)
        strategy = MartingaleStrategy(config)
        game_state = GameState(balance=Decimal("10000"))

        expected_bets = [
            Decimal("1"),
            Decimal("2"),
            Decimal("4"),
            Decimal("8"),
            Decimal("16"),
        ]

        for _, expected in enumerate(expected_bets):
            next_bet = strategy.calculate_next_bet(game_state)
            assert next_bet == expected

            # Simuler une perte
            result = BetResult(
                roll=60.0,
                won=False,
                threshold=49.5,
                amount=next_bet,
                payout=Decimal("0"),
            )
            strategy.update_after_result(result)

    def test_reset_state(self) -> None:
        """Vérifie que reset_state réinitialise correctement"""
        config = StrategyConfig(base_bet=Decimal("2"))
        strategy = MartingaleStrategy(config)

        # Modifier l'état
        strategy.consecutive_losses = 5
        strategy.current_bet = Decimal("32")

        # Reset
        strategy.reset_state()

        assert strategy.consecutive_losses == 0
        assert strategy.current_bet == Decimal("2")
        assert strategy.last_bet == Decimal("2")
