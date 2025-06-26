from decimal import Decimal

from dicebot.core.models import BetResult, GameState
from dicebot.strategies.base import StrategyConfig
from dicebot.strategies.dalembert import DAlembert


class TestDAlembert:
    def test_initialization(self) -> None:
        """Test l'initialisation de la stratégie"""
        config = StrategyConfig(base_bet=Decimal("1"))
        strategy = DAlembert(config)

        assert strategy.current_units == 1
        assert strategy.unit_value == Decimal("1")
        assert strategy.current_bet == Decimal("1")

    def test_increase_on_loss(self) -> None:
        """Vérifie l'augmentation d'une unité après une perte"""
        config = StrategyConfig(base_bet=Decimal("0.5"))
        strategy = DAlembert(config)
        game_state = GameState(balance=Decimal("100"))

        # Mise initiale
        assert strategy.calculate_next_bet(game_state) == Decimal("0.5")

        # Simuler une perte
        result = BetResult(
            roll=60.0,
            won=False,
            threshold=49.5,
            amount=Decimal("0.5"),
            payout=Decimal("0"),
        )
        strategy.update_after_result(result)

        # Devrait augmenter d'une unité
        assert strategy.current_units == 2
        assert strategy.calculate_next_bet(game_state) == Decimal("1.0")

    def test_decrease_on_win(self) -> None:
        """Vérifie la diminution d'une unité après un gain"""
        config = StrategyConfig(base_bet=Decimal("0.5"))
        strategy = DAlembert(config)
        game_state = GameState(balance=Decimal("100"))

        # Augmenter à 3 unités
        strategy.current_units = 3

        # Simuler un gain
        result = BetResult(
            roll=40.0,
            won=True,
            threshold=49.5,
            amount=Decimal("1.5"),
            payout=Decimal("3.0"),
        )
        strategy.update_after_result(result)

        # Devrait diminuer d'une unité
        assert strategy.current_units == 2
        assert strategy.calculate_next_bet(game_state) == Decimal("1.0")

    def test_minimum_units(self) -> None:
        """Vérifie qu'on ne descend pas en dessous de 1 unité"""
        config = StrategyConfig(base_bet=Decimal("1"))
        strategy = DAlembert(config)

        # Déjà à 1 unité
        assert strategy.current_units == 1

        # Simuler un gain
        result = BetResult(
            roll=40.0,
            won=True,
            threshold=49.5,
            amount=Decimal("1"),
            payout=Decimal("2"),
        )
        strategy.update_after_result(result)

        # Devrait rester à 1
        assert strategy.current_units == 1

    def test_maximum_units(self) -> None:
        """Vérifie qu'on ne dépasse pas max_losses unités"""
        config = StrategyConfig(base_bet=Decimal("1"), max_losses=5)
        strategy = DAlembert(config)

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

        # Devrait être plafonné à max_losses
        assert strategy.current_units == 5

    def test_linear_progression(self) -> None:
        """Vérifie la progression linéaire des mises"""
        config = StrategyConfig(base_bet=Decimal("0.1"))
        strategy = DAlembert(config)
        game_state = GameState(balance=Decimal("100"))

        expected_bets = [
            Decimal("0.1"),  # 1 unité
            Decimal("0.2"),  # 2 unités
            Decimal("0.3"),  # 3 unités
            Decimal("0.4"),  # 4 unités
        ]

        for expected in expected_bets:
            bet = strategy.calculate_next_bet(game_state)
            assert bet == expected

            # Simuler une perte pour augmenter
            result = BetResult(
                roll=60.0, won=False, threshold=49.5, amount=bet, payout=Decimal("0")
            )
            strategy.update_after_result(result)

    def test_alternating_wins_losses(self) -> None:
        """Teste le comportement avec alternance gains/pertes"""
        config = StrategyConfig(base_bet=Decimal("1"))
        strategy = DAlembert(config)

        # Perte -> 2 unités
        result_loss = BetResult(
            roll=60.0,
            won=False,
            threshold=49.5,
            amount=Decimal("1"),
            payout=Decimal("0"),
        )
        strategy.update_after_result(result_loss)
        assert strategy.current_units == 2

        # Gain -> 1 unité
        result_win = BetResult(
            roll=40.0,
            won=True,
            threshold=49.5,
            amount=Decimal("2"),
            payout=Decimal("4"),
        )
        strategy.update_after_result(result_win)
        assert strategy.current_units == 1

        # Perte -> 2 unités
        strategy.update_after_result(result_loss)
        assert strategy.current_units == 2

    def test_reset_state(self) -> None:
        """Vérifie que reset_state réinitialise correctement"""
        config = StrategyConfig(base_bet=Decimal("2"))
        strategy = DAlembert(config)

        # Modifier l'état
        strategy.current_units = 5
        strategy.current_bet = Decimal("10")

        # Reset
        strategy.reset_state()

        assert strategy.current_units == 1
        assert strategy.current_bet == Decimal("2")

    def test_get_current_units(self) -> None:
        """Teste la méthode d'information"""
        config = StrategyConfig(base_bet=Decimal("1"))
        strategy = DAlembert(config)

        strategy.current_units = 3
        assert strategy.get_current_units() == 3
