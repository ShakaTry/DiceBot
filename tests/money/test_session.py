from decimal import Decimal

from dicebot.core import BetResult
from dicebot.money import Session, SessionConfig


class TestSession:
    def test_initialization(self) -> None:
        config = SessionConfig(initial_bankroll=Decimal("10"))
        session = Session("test_session", config)

        assert session.state.session_id == "test_session"
        assert session.state.is_active
        assert session.state.initial_bankroll == Decimal("10")
        assert session.state.game_state.balance == Decimal("10")

    def test_should_stop_max_bets(self) -> None:
        config = SessionConfig(initial_bankroll=Decimal("10"), max_bets=5)
        session = Session("test", config)

        # Simulate 5 bets
        for _ in range(5):
            result = BetResult(
                roll=50.0,
                won=True,
                threshold=49.5,
                amount=Decimal("1"),
                payout=Decimal("2"),
            )
            session.process_bet(result)

        assert not session.state.is_active
        assert session.state.stop_reason == "Max bets reached"

    def test_should_stop_stop_loss(self) -> None:
        config = SessionConfig(
            initial_bankroll=Decimal("10"),
            stop_loss=-0.5,  # -50%
        )
        session = Session("test", config)

        # Simulate losses
        for _ in range(5):
            result = BetResult(
                roll=60.0,
                won=False,
                threshold=49.5,
                amount=Decimal("1"),
                payout=Decimal("0"),
            )
            session.process_bet(result)

        assert not session.state.is_active
        assert session.state.stop_reason is not None
        assert "Stop loss triggered" in session.state.stop_reason

    def test_should_stop_take_profit(self) -> None:
        config = SessionConfig(
            initial_bankroll=Decimal("10"),
            take_profit=0.5,  # +50%
        )
        session = Session("test", config)

        # Simulate wins
        for _ in range(5):
            result = BetResult(
                roll=40.0,
                won=True,
                threshold=49.5,
                amount=Decimal("1"),
                payout=Decimal("2"),
            )
            session.process_bet(result)

        assert not session.state.is_active
        assert session.state.stop_reason is not None
        assert "Take profit triggered" in session.state.stop_reason

    def test_should_stop_consecutive_losses(self) -> None:
        config = SessionConfig(initial_bankroll=Decimal("10"), max_consecutive_losses=3)
        session = Session("test", config)

        # Simulate 3 consecutive losses
        for _ in range(3):
            result = BetResult(
                roll=60.0,
                won=False,
                threshold=49.5,
                amount=Decimal("1"),
                payout=Decimal("0"),
            )
            session.process_bet(result)

        assert not session.state.is_active
        assert session.state.stop_reason is not None
        assert "Max consecutive losses reached" in session.state.stop_reason

    def test_process_bet(self) -> None:
        config = SessionConfig(initial_bankroll=Decimal("10"))
        session = Session("test", config)

        # Win bet
        result = BetResult(
            roll=40.0,
            won=True,
            threshold=49.5,
            amount=Decimal("1"),
            payout=Decimal("2"),
        )
        session.process_bet(result)

        assert session.state.game_state.balance == Decimal("11")
        assert session.state.game_state.wins_count == 1
        assert session.state.game_state.total_wagered == Decimal("1")

        # Loss bet
        result = BetResult(
            roll=60.0,
            won=False,
            threshold=49.5,
            amount=Decimal("1"),
            payout=Decimal("0"),
        )
        session.process_bet(result)

        assert session.state.game_state.balance == Decimal("10")
        assert session.state.game_state.losses_count == 1
        assert session.state.game_state.total_wagered == Decimal("2")

    def test_metrics(self) -> None:
        config = SessionConfig(initial_bankroll=Decimal("10"))
        session = Session("test", config)

        # Run some bets
        for i in range(3):
            result = BetResult(
                roll=40.0 if i % 2 == 0 else 60.0,
                won=i % 2 == 0,
                threshold=49.5,
                amount=Decimal("1"),
                payout=Decimal("2") if i % 2 == 0 else Decimal("0"),
            )
            session.process_bet(result)

        metrics = session.get_metrics()

        assert metrics["session_id"] == "test"
        assert metrics["is_active"] is True
        assert metrics["bets_count"] == 3
        assert metrics["wins_count"] == 2
        assert metrics["losses_count"] == 1
        assert metrics["total_wagered"] == 3.0
        assert metrics["roi"] == 0.1  # 10% profit
