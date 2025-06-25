from decimal import Decimal

from dicebot.core.models import BetResult, GameState
from dicebot.strategies.base import StrategyConfig
from dicebot.strategies.fibonacci import FibonacciStrategy


class TestFibonacciStrategy:
    def test_initialization(self):
        """Test l'initialisation de la stratégie"""
        config = StrategyConfig(base_bet=Decimal("1"))
        strategy = FibonacciStrategy(config)

        assert strategy.current_index == 0
        assert strategy.current_bet == Decimal("1")
        assert len(strategy.sequence) > 0
        assert strategy.sequence[0] == 1
        assert strategy.sequence[1] == 1

    def test_sequence_limited_by_max_losses(self):
        """Vérifie que la séquence est limitée par max_losses"""
        config = StrategyConfig(base_bet=Decimal("1"), max_losses=5)
        strategy = FibonacciStrategy(config)

        assert len(strategy.sequence) == 5
        assert strategy.sequence == [1, 1, 2, 3, 5]

    def test_advance_on_loss(self):
        """Vérifie l'avancement dans la séquence après une perte"""
        config = StrategyConfig(base_bet=Decimal("1"))
        strategy = FibonacciStrategy(config)
        game_state = GameState(balance=Decimal("100"))

        # Position initiale
        assert strategy.current_index == 0
        assert strategy.calculate_next_bet(game_state) == Decimal("1")

        # Simuler une perte
        result = BetResult(
            roll=60.0,
            won=False,
            threshold=49.5,
            amount=Decimal("1"),
            payout=Decimal("0"),
        )
        strategy.update_after_result(result)

        # Devrait avancer à l'index 1
        assert strategy.current_index == 1
        assert strategy.calculate_next_bet(game_state) == Decimal("1")  # Fib[1] = 1

        # Une autre perte
        strategy.update_after_result(result)
        assert strategy.current_index == 2
        assert strategy.calculate_next_bet(game_state) == Decimal("2")  # Fib[2] = 2

    def test_retreat_on_win(self):
        """Vérifie le recul dans la séquence après un gain"""
        config = StrategyConfig(base_bet=Decimal("1"))
        strategy = FibonacciStrategy(config)
        game_state = GameState(balance=Decimal("100"))

        # Avancer à l'index 5
        strategy.current_index = 5  # Fib[5] = 8

        # Simuler un gain
        result = BetResult(
            roll=40.0,
            won=True,
            threshold=49.5,
            amount=Decimal("8"),
            payout=Decimal("16"),
        )
        strategy.update_after_result(result)

        # Devrait reculer de 2 positions
        assert strategy.current_index == 3  # 5 - 2 = 3
        assert strategy.calculate_next_bet(game_state) == Decimal("3")  # Fib[3] = 3

    def test_retreat_at_beginning(self):
        """Vérifie qu'on ne peut pas reculer en dessous de 0"""
        config = StrategyConfig(base_bet=Decimal("1"))
        strategy = FibonacciStrategy(config)

        # Positions proches du début
        strategy.current_index = 1

        # Simuler un gain
        result = BetResult(
            roll=40.0,
            won=True,
            threshold=49.5,
            amount=Decimal("1"),
            payout=Decimal("2"),
        )
        strategy.update_after_result(result)

        # Devrait être à 0 (pas négatif)
        assert strategy.current_index == 0

    def test_max_sequence_boundary(self):
        """Vérifie qu'on ne dépasse pas la fin de la séquence"""
        config = StrategyConfig(base_bet=Decimal("1"), max_losses=5)
        strategy = FibonacciStrategy(config)

        # Simuler beaucoup de pertes
        for _ in range(10):
            result = BetResult(
                roll=60.0,
                won=False,
                threshold=49.5,
                amount=Decimal("1"),
                payout=Decimal("0"),
            )
            strategy.update_after_result(result)

        # Devrait être au maximum de la séquence
        assert strategy.current_index == 4  # Max index pour une séquence de 5

    def test_fibonacci_progression(self):
        """Vérifie que les mises suivent bien la séquence de Fibonacci"""
        config = StrategyConfig(base_bet=Decimal("0.1"))
        strategy = FibonacciStrategy(config)
        game_state = GameState(balance=Decimal("1000"))

        expected_sequence = [
            Decimal("0.1"),  # 1 * 0.1
            Decimal("0.1"),  # 1 * 0.1
            Decimal("0.2"),  # 2 * 0.1
            Decimal("0.3"),  # 3 * 0.1
            Decimal("0.5"),  # 5 * 0.1
            Decimal("0.8"),  # 8 * 0.1
        ]

        for expected in expected_sequence:
            bet = strategy.calculate_next_bet(game_state)
            assert bet == expected

            # Simuler une perte pour avancer
            result = BetResult(
                roll=60.0, won=False, threshold=49.5, amount=bet, payout=Decimal("0")
            )
            strategy.update_after_result(result)

    def test_reset_state(self):
        """Vérifie que reset_state réinitialise correctement"""
        config = StrategyConfig(base_bet=Decimal("2"))
        strategy = FibonacciStrategy(config)

        # Modifier l'état
        strategy.current_index = 5
        strategy.current_bet = Decimal("16")

        # Reset
        strategy.reset_state()

        assert strategy.current_index == 0
        assert strategy.current_bet == Decimal("2")

    def test_get_info_methods(self):
        """Teste les méthodes d'information"""
        config = StrategyConfig(base_bet=Decimal("1"))
        strategy = FibonacciStrategy(config)

        strategy.current_index = 4

        assert strategy.get_current_level() == 4
        assert strategy.get_sequence_value() == 5  # Fib[4] = 5
