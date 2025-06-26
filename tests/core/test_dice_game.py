from decimal import Decimal

import pytest

from dicebot.core import BetResult, DiceGame, GameConfig


class TestDiceGame:
    def test_initialization(self) -> None:
        game = DiceGame(use_provably_fair=False)  # Mode legacy pour tests
        assert game.house_edge == 0.01
        assert isinstance(game.config, GameConfig)

    def test_calculate_win_chance(self) -> None:
        game = DiceGame(use_provably_fair=False)

        # Test 2x multiplier (utiliser méthode legacy)
        chance = game.calculate_win_chance_from_multiplier(2.0)
        expected = 50.0 * (1 - 0.01)  # 49.5%
        assert abs(chance - expected) < 0.001

        # Test 10x multiplier
        chance = game.calculate_win_chance_from_multiplier(10.0)
        expected = 10.0 * (1 - 0.01)  # 9.9%
        assert abs(chance - expected) < 0.001

    def test_invalid_multiplier(self) -> None:
        game = DiceGame(use_provably_fair=False)

        with pytest.raises(ValueError):
            game.calculate_win_chance_from_multiplier(0.5)  # Too low

        with pytest.raises(ValueError):
            game.calculate_win_chance_from_multiplier(100.0)  # Too high

    def test_roll_win(self) -> None:
        game = DiceGame(seed=42)  # Fixed seed for reproducibility

        result = game.roll(Decimal("1"), 2.0)
        assert isinstance(result, BetResult)
        assert result.amount == Decimal("1")
        assert 0 <= result.roll <= 100

        if result.won:
            assert result.payout == Decimal("2")
        else:
            assert result.payout == Decimal("0")

    def test_bet_limits(self) -> None:
        game = DiceGame(use_provably_fair=False)

        # Test minimum bet
        with pytest.raises(ValueError, match="Minimum bet"):
            game.roll(Decimal("0.00001"), 2.0)

        # Test maximum bet
        with pytest.raises(ValueError, match="Maximum bet"):
            game.roll(Decimal("10000"), 2.0)

    def test_expected_value(self) -> None:
        game = DiceGame(use_provably_fair=False)

        # EV should be negative due to house edge
        ev = game.expected_value_legacy(Decimal("1"), 2.0)
        assert ev < 0

        # With constant house edge, all bets have same EV (-1% of bet)
        ev_2x = game.expected_value_legacy(Decimal("1"), 2.0)
        ev_10x = game.expected_value_legacy(Decimal("1"), 10.0)
        # Both should be -0.01 (1% of bet)
        assert abs(ev_2x - Decimal("-0.01")) < Decimal("0.001")
        assert abs(ev_10x - Decimal("-0.01")) < Decimal("0.001")

    def test_kelly_criterion(self) -> None:
        game = DiceGame(use_provably_fair=False)

        bankroll = Decimal("100")

        # Kelly should return 0 for negative EV bets
        kelly_bet = game.kelly_criterion_legacy(bankroll, 2.0)
        assert kelly_bet == Decimal("0")

        # If we had positive EV (impossible with house edge), kelly would be positive
        # This is just to test the math works
        game.house_edge = -0.01  # Negative house edge for testing
        kelly_bet = game.kelly_criterion_legacy(bankroll, 2.0)
        assert kelly_bet > Decimal("0")
        assert kelly_bet < bankroll * Decimal("0.1")  # Safety cap at 10%
