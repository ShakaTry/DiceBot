"""Tests pour le système OVER/UNDER."""

from decimal import Decimal

import pytest

from dicebot.core import BetType, DiceGame, GameState
from dicebot.strategies import StrategyConfig, StrategyFactory


class TestDiceGameOverUnder:
    """Test le support OVER/UNDER dans DiceGame."""

    def test_roll_under(self) -> None:
        """Test d'un pari UNDER."""
        game = DiceGame(use_provably_fair=False, seed=42)

        # Pari UNDER avec target 50
        result = game.roll(Decimal("1"), 50.0, BetType.UNDER)

        assert result.bet_type == BetType.UNDER
        assert result.target == 50.0
        assert 0.0 <= result.roll <= 100.0

        # Vérifier la logique de victoire
        if result.roll < 50.0:
            assert result.won
            assert result.payout > Decimal("0")
        else:
            assert not result.won
            assert result.payout == Decimal("0")

    def test_roll_over(self) -> None:
        """Test d'un pari OVER."""
        game = DiceGame(use_provably_fair=False, seed=42)

        # Pari OVER avec target 50
        result = game.roll(Decimal("1"), 50.0, BetType.OVER)

        assert result.bet_type == BetType.OVER
        assert result.target == 50.0

        # Vérifier la logique de victoire
        if result.roll > 50.0:
            assert result.won
            assert result.payout > Decimal("0")
        else:
            assert not result.won
            assert result.payout == Decimal("0")

    def test_win_chance_calculation(self) -> None:
        """Test du calcul des probabilités OVER/UNDER."""
        game = DiceGame(use_provably_fair=False)

        # UNDER 50 devrait avoir ~49.5% (avec house edge 1%)
        under_chance = game.calculate_win_chance(50.0, BetType.UNDER)
        expected_under = 50.0 * (1 - 0.01)  # 49.5%
        assert abs(under_chance - expected_under) < 0.001

        # OVER 50 devrait avoir ~49.5% (avec house edge 1%)
        over_chance = game.calculate_win_chance(50.0, BetType.OVER)
        expected_over = 50.0 * (1 - 0.01)  # 49.5%
        assert abs(over_chance - expected_over) < 0.001

        # UNDER 25 devrait avoir ~24.75%
        under_25_chance = game.calculate_win_chance(25.0, BetType.UNDER)
        expected_under_25 = 25.0 * (1 - 0.01)  # 24.75%
        assert abs(under_25_chance - expected_under_25) < 0.001

        # OVER 75 devrait avoir ~24.75%
        over_75_chance = game.calculate_win_chance(75.0, BetType.OVER)
        expected_over_75 = 25.0 * (1 - 0.01)  # 24.75%
        assert abs(over_75_chance - expected_over_75) < 0.001

    def test_multiplier_conversion(self) -> None:
        """Test de la conversion target <-> multiplier."""
        game = DiceGame(use_provably_fair=False)

        # Test UNDER - pour multiplier 2x, target devrait être 50
        target_from_2x = game.target_from_multiplier(2.0, BetType.UNDER)
        assert abs(target_from_2x - 50.0) < 0.1  # Devrait être 50.0

        # Test OVER - pour multiplier 2x, target devrait être 50
        target_from_2x_over = game.target_from_multiplier(2.0, BetType.OVER)
        assert abs(target_from_2x_over - 50.0) < 0.1  # Devrait être 50.0

        # Test conversion inverse - UNDER 50 avec house edge
        multiplier_from_50 = game.multiplier_from_target(50.0, BetType.UNDER)
        # Avec house edge 1%, win_chance = 50 * 0.99 = 49.5%, donc multiplier ≈ 100/49.5 ≈ 2.02
        assert abs(multiplier_from_50 - 2.02) < 0.1

    def test_edge_cases(self) -> None:
        """Test des cas limites."""
        game = DiceGame(use_provably_fair=False)

        # Target très bas
        result_low = game.roll(Decimal("1"), 1.0, BetType.UNDER)
        assert result_low.target == 1.0

        # Target très haut
        result_high = game.roll(Decimal("1"), 99.0, BetType.OVER)
        assert result_high.target == 99.0

        # Target invalide
        with pytest.raises(ValueError):
            game.roll(Decimal("1"), 0.0, BetType.UNDER)

        with pytest.raises(ValueError):
            game.roll(Decimal("1"), 100.0, BetType.UNDER)

    def test_legacy_compatibility(self) -> None:
        """Test que l'ancienne interface fonctionne encore."""
        game = DiceGame(use_provably_fair=False, seed=42)

        # Utiliser la méthode legacy
        result = game.roll_legacy(Decimal("1"), 2.0)

        assert result.bet_type == BetType.UNDER
        assert (
            result.multiplier is not None and abs(result.multiplier - 2.0) < 0.1
        )  # Tolérance pour approximations
        assert result.target > 0

        # Expected value legacy
        ev = game.expected_value_legacy(Decimal("1"), 2.0)
        assert ev < 0  # Négatif à cause du house edge


class TestStrategyOverUnder:
    """Test le support OVER/UNDER dans les stratégies."""

    def test_strategy_default_behavior(self) -> None:
        """Test que les stratégies utilisent les paramètres par défaut."""
        config = StrategyConfig(base_bet=Decimal("1"))
        strategy = StrategyFactory.create("flat", config)

        game_state = GameState(balance=Decimal("100"))
        decision = strategy.decide_bet(game_state)

        assert not decision.skip
        assert decision.bet_type == BetType.UNDER  # Défaut
        assert decision.target == 50.0  # Défaut
        assert decision.amount == Decimal("1")

    def test_strategy_custom_config(self) -> None:
        """Test des stratégies avec configuration OVER/UNDER personnalisée."""
        config = StrategyConfig(
            base_bet=Decimal("1"), default_bet_type=BetType.OVER, default_target=75.0
        )
        strategy = StrategyFactory.create("flat", config)

        game_state = GameState(balance=Decimal("100"))
        decision = strategy.decide_bet(game_state)

        assert decision.bet_type == BetType.OVER
        assert decision.target == 75.0

    def test_martingale_over_under(self) -> None:
        """Test Martingale avec OVER/UNDER."""
        config = StrategyConfig(
            base_bet=Decimal("1"),
            max_losses=5,  # Réduire pour éviter les validations strictes
            default_bet_type=BetType.UNDER,
            default_target=49.0,
        )
        strategy = StrategyFactory.create("martingale", config)

        # Premier pari
        game_state = GameState(balance=Decimal("100"))
        decision1 = strategy.decide_bet(game_state)

        assert decision1.amount == Decimal("1")
        assert decision1.bet_type == BetType.UNDER
        assert decision1.target == 49.0

        # Simuler une perte
        from dicebot.core.models import BetResult

        loss_result = BetResult(
            roll=50.0,
            won=False,
            threshold=49.0,
            amount=Decimal("1"),
            payout=Decimal("0"),
            bet_type=BetType.UNDER,
            target=49.0,
        )

        strategy.update_after_result(loss_result)
        game_state.update(loss_result)

        # Deuxième pari (doublé après perte)
        decision2 = strategy.decide_bet(game_state)
        assert decision2.amount == Decimal("2")  # Doublé
        assert decision2.bet_type == BetType.UNDER  # Même type

    def test_composite_strategy_over_under(self) -> None:
        """Test CompositeStrategy avec OVER/UNDER."""
        from dicebot.strategies.composite import (
            CombinationMode,
            CompositeConfig,
            CompositeStrategy,
        )

        # Créer deux stratégies avec types différents
        config1 = StrategyConfig(
            base_bet=Decimal("1"), default_bet_type=BetType.UNDER, default_target=30.0
        )
        config2 = StrategyConfig(
            base_bet=Decimal("1"), default_bet_type=BetType.OVER, default_target=70.0
        )

        strategy1 = StrategyFactory.create("flat", config1)
        strategy2 = StrategyFactory.create("flat", config2)

        # Stratégie composite en mode majorité
        composite_config = CompositeConfig(base_bet=Decimal("1"), mode=CombinationMode.AVERAGE)
        composite = CompositeStrategy(composite_config, [strategy1, strategy2])

        game_state = GameState(balance=Decimal("100"))
        decision = composite.decide_bet(game_state)

        assert not decision.skip
        # Devrait être une moyenne des deux approaches
        assert decision.amount == Decimal("1")
        # Le type devrait être celui avec la majorité (ou premier en cas d'égalité)
        assert decision.bet_type in [BetType.UNDER, BetType.OVER]
        # Target devrait être proche de la moyenne (50.0)
        assert 40.0 <= decision.target <= 60.0


class TestOverUnderMath:
    """Test des calculs mathématiques OVER/UNDER."""

    def test_probability_symmetry(self) -> None:
        """Test que OVER et UNDER sont symétriques."""
        game = DiceGame(use_provably_fair=False)

        # UNDER 30 et OVER 70 devraient avoir la même probabilité
        under_30 = game.calculate_win_chance(30.0, BetType.UNDER)
        over_70 = game.calculate_win_chance(70.0, BetType.OVER)

        assert abs(under_30 - over_70) < 0.001

        # UNDER 25 et OVER 75 devraient avoir la même probabilité
        under_25 = game.calculate_win_chance(25.0, BetType.UNDER)
        over_75 = game.calculate_win_chance(75.0, BetType.OVER)

        assert abs(under_25 - over_75) < 0.001

    def test_total_probability(self) -> None:
        """Test que UNDER + OVER pour un même point ≈ 99% (avec house edge)."""
        game = DiceGame(use_provably_fair=False)

        # Pour target 50
        under_50 = game.calculate_win_chance(50.0, BetType.UNDER)
        over_50 = game.calculate_win_chance(50.0, BetType.OVER)

        # Total devrait être ≈ 99% (100% - 1% house edge)
        total = under_50 + over_50
        assert abs(total - 99.0) < 0.1

    def test_expected_value_negative(self) -> None:
        """Test que toutes les EV sont négatives (house edge)."""
        game = DiceGame(use_provably_fair=False)

        # Test différentes configurations
        test_cases = [
            (25.0, BetType.UNDER),
            (50.0, BetType.UNDER),
            (75.0, BetType.UNDER),
            (25.0, BetType.OVER),
            (50.0, BetType.OVER),
            (75.0, BetType.OVER),
        ]

        for target, bet_type in test_cases:
            ev = game.expected_value(Decimal("1"), target, bet_type)
            assert ev < 0, f"EV should be negative for {target} {bet_type.value}"
            # EV devrait être environ -1% du pari
            assert abs(ev + Decimal("0.01")) < Decimal("0.005")
