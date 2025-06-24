from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from ..core.constants import (
    DEFAULT_MAX_BETS_PER_SESSION,
    DEFAULT_STOP_LOSS,
    DEFAULT_TAKE_PROFIT,
)
from ..core.models import BetResult, GameState


@dataclass
class SessionConfig:
    initial_bankroll: Decimal
    stop_loss: float = DEFAULT_STOP_LOSS
    take_profit: float = DEFAULT_TAKE_PROFIT
    max_bets: int = DEFAULT_MAX_BETS_PER_SESSION
    max_consecutive_losses: int | None = None


@dataclass
class SessionState:
    session_id: str
    start_time: datetime
    end_time: datetime | None = None
    initial_bankroll: Decimal = Decimal("0")
    final_bankroll: Decimal | None = None
    game_state: GameState = field(
        default_factory=lambda: GameState(balance=Decimal("0"))
    )
    stop_reason: str | None = None

    @property
    def is_active(self) -> bool:
        return self.end_time is None

    @property
    def duration(self) -> float | None:
        if not self.end_time:
            return None
        return (self.end_time - self.start_time).total_seconds()

    @property
    def profit(self) -> Decimal:
        if self.final_bankroll is None:
            return self.game_state.balance - self.initial_bankroll
        return self.final_bankroll - self.initial_bankroll

    @property
    def roi(self) -> float:
        if self.initial_bankroll == 0:
            return 0.0
        return float(self.profit / self.initial_bankroll)


class Session:
    def __init__(self, session_id: str, config: SessionConfig):
        self.config = config
        self.state = SessionState(
            session_id=session_id,
            start_time=datetime.now(),
            initial_bankroll=config.initial_bankroll,
            game_state=GameState(balance=config.initial_bankroll),
        )

    def should_stop(self) -> tuple[bool, str | None]:
        if not self.state.is_active:
            return True, "Session already ended"

        # Check max bets
        if self.state.game_state.bets_count >= self.config.max_bets:
            return True, "Max bets reached"

        # Check stop loss
        current_balance = self.state.game_state.balance
        loss_ratio = float(
            (current_balance - self.state.initial_bankroll)
            / self.state.initial_bankroll
        )
        if loss_ratio <= self.config.stop_loss:
            return True, f"Stop loss triggered ({loss_ratio:.2%})"

        # Check take profit
        if loss_ratio >= self.config.take_profit:
            return True, f"Take profit triggered ({loss_ratio:.2%})"

        # Check consecutive losses
        if (
            self.config.max_consecutive_losses is not None
            and self.state.game_state.consecutive_losses
            >= self.config.max_consecutive_losses
        ):
            return (
                True,
                f"Max consecutive losses reached "
                f"({self.state.game_state.consecutive_losses})",
            )

        # Check if bankroll is too low to bet
        if current_balance <= 0:
            return True, "Bankroll depleted"

        return False, None

    def process_bet(self, result: BetResult) -> None:
        if not self.state.is_active:
            raise ValueError("Cannot process bet on inactive session")

        self.state.game_state.update(result)

        # Check if session should stop after this bet
        should_stop, reason = self.should_stop()
        if should_stop:
            self.end(reason)

    def end(self, reason: str | None = None) -> None:
        if not self.state.is_active:
            return

        self.state.end_time = datetime.now()
        self.state.final_bankroll = self.state.game_state.balance
        self.state.stop_reason = reason or "Manual stop"

    def get_metrics(self) -> dict:
        game_state = self.state.game_state

        metrics = {
            "session_id": self.state.session_id,
            "is_active": self.state.is_active,
            "start_time": self.state.start_time.isoformat(),
            "end_time": (
                self.state.end_time.isoformat() if self.state.end_time else None
            ),
            "duration": self.state.duration,
            "initial_bankroll": float(self.state.initial_bankroll),
            "final_bankroll": (
                float(self.state.final_bankroll)
                if self.state.final_bankroll
                else float(game_state.balance)
            ),
            "profit": float(self.state.profit),
            "roi": self.state.roi,
            "bets_count": game_state.bets_count,
            "wins_count": game_state.wins_count,
            "losses_count": game_state.losses_count,
            "win_rate": game_state.win_rate,
            "total_wagered": float(game_state.total_wagered),
            "max_balance": float(game_state.max_balance),
            "min_balance": float(game_state.min_balance),
            "max_drawdown": (
                float(
                    (game_state.max_balance - game_state.min_balance)
                    / game_state.max_balance
                )
                if game_state.max_balance > 0
                else 0
            ),
            "consecutive_wins_max": game_state.consecutive_wins,
            "consecutive_losses_max": game_state.consecutive_losses,
            "stop_reason": self.state.stop_reason,
        }

        return metrics
