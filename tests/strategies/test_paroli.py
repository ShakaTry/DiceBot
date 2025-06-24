from decimal import Decimal

from dicebot.core.models import BetResult, GameState
from dicebot.strategies.base import StrategyConfig
from dicebot.strategies.paroli import ParoliStrategy


class TestParoliStrategy:
    def test_initialization(self):
        """Test l'initialisation de la stratégie"""
        config = StrategyConfig(base_bet=Decimal("1"))
        strategy = ParoliStrategy(config, target_wins=3)

        assert strategy.consecutive_wins == 0
        assert strategy.target_wins == 3
        assert strategy.current_bet == Decimal("1")

    def test_double_after_win(self):
        """Vérifie que la mise double après un gain"""
        config = StrategyConfig(base_bet=Decimal("1"), multiplier=2.0)
        strategy = ParoliStrategy(config)
        game_state = GameState(balance=Decimal("100"))

        # Simuler un gain
        result = BetResult(
            roll=40.0,
            won=True,
            threshold=49.5,
            amount=Decimal("1"),
            payout=Decimal("2"),
        )
        strategy.update_after_result(result)

        # La prochaine mise devrait être doublée
        assert strategy.consecutive_wins == 1
        next_bet = strategy.calculate_next_bet(game_state)
        assert next_bet == Decimal("2")

    def test_reset_after_loss(self):
        """Vérifie que la mise revient à la base après une perte"""
        config = StrategyConfig(base_bet=Decimal("1"))
        strategy = ParoliStrategy(config)
        game_state = GameState(balance=Decimal("100"))

        # Simuler quelques gains
        for _ in range(2):
            result = BetResult(
                roll=40.0,
                won=True,
                threshold=49.5,
                amount=Decimal("1"),
                payout=Decimal("2"),
            )
            strategy.update_after_result(result)

        assert strategy.consecutive_wins == 2

        # Simuler une perte
        result = BetResult(
            roll=60.0,
            won=False,
            threshold=49.5,
            amount=Decimal("4"),
            payout=Decimal("0"),
        )
        strategy.update_after_result(result)

        # Devrait être reset
        assert strategy.consecutive_wins == 0
        next_bet = strategy.calculate_next_bet(game_state)
        assert next_bet == Decimal("1")

    def test_reset_after_target_wins(self):
        """Vérifie le reset après avoir atteint l'objectif"""
        config = StrategyConfig(base_bet=Decimal("1"))
        strategy = ParoliStrategy(config, target_wins=3)
        game_state = GameState(balance=Decimal("100"))

        # Simuler 3 gains consécutifs
        for i in range(3):
            result = BetResult(
                roll=40.0,
                won=True,
                threshold=49.5,
                amount=Decimal(str(2**i)),  # 1, 2, 4
                payout=Decimal(str(2 ** (i + 1))),  # 2, 4, 8
            )
            strategy.update_after_result(result)

        assert strategy.consecutive_wins == 3

        # La prochaine mise devrait être la base
        next_bet = strategy.calculate_next_bet(game_state)
        assert next_bet == Decimal("1")

    def test_progression_sequence(self):
        """Vérifie la progression géométrique des mises"""
        config = StrategyConfig(base_bet=Decimal("0.5"), multiplier=2.0)
        strategy = ParoliStrategy(config, target_wins=4)
        game_state = GameState(balance=Decimal("100"))

        expected_bets = [Decimal("0.5"), Decimal("1"), Decimal("2"), Decimal("4")]

        for _, expected in enumerate(expected_bets):
            bet = strategy.calculate_next_bet(game_state)
            assert bet == expected

            # Simuler un gain pour continuer la progression
            result = BetResult(roll=40.0, won=True, threshold=49.5, amount=bet, payout=bet * 2)
            strategy.update_after_result(result)

    def test_get_info_methods(self):
        """Teste les méthodes d'information"""
        config = StrategyConfig(base_bet=Decimal("1"))
        strategy = ParoliStrategy(config, target_wins=5)

        assert strategy.get_target_wins() == 5

        strategy.consecutive_wins = 3
        assert strategy.get_consecutive_wins() == 3
