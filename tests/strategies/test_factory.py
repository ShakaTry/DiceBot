from decimal import Decimal

import pytest

from dicebot.strategies.base import StrategyConfig
from dicebot.strategies.dalembert import DAlembert
from dicebot.strategies.factory import StrategyFactory
from dicebot.strategies.fibonacci import FibonacciStrategy
from dicebot.strategies.flat import FlatBetting
from dicebot.strategies.martingale import MartingaleStrategy
from dicebot.strategies.paroli import ParoliStrategy


class TestStrategyFactory:
    def test_create_martingale(self):
        """Test la création d'une stratégie Martingale"""
        config = StrategyConfig(base_bet=Decimal("1"), max_losses=5)
        strategy = StrategyFactory.create("martingale", config)

        assert isinstance(strategy, MartingaleStrategy)
        assert strategy.config.base_bet == Decimal("1")

    def test_create_fibonacci(self):
        """Test la création d'une stratégie Fibonacci"""
        config = StrategyConfig(base_bet=Decimal("2"))
        strategy = StrategyFactory.create("fibonacci", config)

        assert isinstance(strategy, FibonacciStrategy)
        assert strategy.config.base_bet == Decimal("2")

    def test_create_dalembert(self):
        """Test la création d'une stratégie D'Alembert"""
        config = StrategyConfig(base_bet=Decimal("0.5"))
        strategy = StrategyFactory.create("dalembert", config)

        assert isinstance(strategy, DAlembert)
        assert strategy.config.base_bet == Decimal("0.5")

    def test_create_flat(self):
        """Test la création d'une stratégie Flat"""
        config = StrategyConfig(base_bet=Decimal("1"))
        strategy = StrategyFactory.create("flat", config)

        assert isinstance(strategy, FlatBetting)

    def test_create_paroli_with_target(self):
        """Test la création d'une stratégie Paroli avec paramètre spécifique"""
        config = StrategyConfig(base_bet=Decimal("1"))
        strategy = StrategyFactory.create("paroli", config, target_wins=5)

        assert isinstance(strategy, ParoliStrategy)
        assert strategy.target_wins == 5

    def test_unknown_strategy(self):
        """Test avec une stratégie inconnue"""
        config = StrategyConfig(base_bet=Decimal("1"))

        with pytest.raises(ValueError) as exc_info:
            StrategyFactory.create("unknown", config)

        assert "Unknown strategy: 'unknown'" in str(exc_info.value)
        assert "Available strategies:" in str(exc_info.value)

    def test_list_available(self):
        """Test la liste des stratégies disponibles"""
        available = StrategyFactory.list_available()

        assert "martingale" in available
        assert "fibonacci" in available
        assert "dalembert" in available
        assert "flat" in available
        assert "paroli" in available
        assert len(available) >= 5

    def test_create_from_dict(self):
        """Test la création depuis un dictionnaire"""
        config_dict = {
            "strategy": "martingale",
            "base_bet": "1.5",
            "max_losses": 5,
            "multiplier": 2.5,
        }

        strategy = StrategyFactory.create_from_dict(config_dict)

        assert isinstance(strategy, MartingaleStrategy)
        assert strategy.config.base_bet == Decimal("1.5")
        assert strategy.config.max_losses == 5
        assert strategy.config.multiplier == 2.5

    def test_create_from_dict_with_decimal(self):
        """Test avec Decimal déjà présent dans le dict"""
        config_dict = {"strategy": "fibonacci", "base_bet": Decimal("0.1")}

        strategy = StrategyFactory.create_from_dict(config_dict)

        assert isinstance(strategy, FibonacciStrategy)
        assert strategy.config.base_bet == Decimal("0.1")

    def test_create_paroli_from_dict(self):
        """Test la création de Paroli avec paramètres spéciaux depuis dict"""
        config_dict = {"strategy": "paroli", "base_bet": "2", "target_wins": 4}

        strategy = StrategyFactory.create_from_dict(config_dict)

        assert isinstance(strategy, ParoliStrategy)
        assert strategy.config.base_bet == Decimal("2")
        assert strategy.target_wins == 4

    def test_register_custom_strategy(self):
        """Test l'enregistrement d'une stratégie personnalisée"""
        # Créer une stratégie custom
        from dicebot.strategies.base import BaseStrategy

        class CustomStrategy(BaseStrategy):
            def calculate_next_bet(self, game_state):
                return self.config.base_bet

            def _update_strategy_state(self, result):
                pass

            def reset_state(self):
                pass

        # L'enregistrer
        StrategyFactory.register_strategy("custom", CustomStrategy)

        # Vérifier qu'elle est disponible
        assert "custom" in StrategyFactory.list_available()

        # La créer
        config = StrategyConfig(base_bet=Decimal("1"))
        strategy = StrategyFactory.create("custom", config)
        assert isinstance(strategy, CustomStrategy)
