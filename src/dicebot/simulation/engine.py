"""
Simulation engine for running dice game simulations with strategies.
"""

import uuid
from concurrent.futures import ProcessPoolExecutor, as_completed
from decimal import Decimal
from multiprocessing import cpu_count
from typing import Any

from ..core.dice_game import DiceGame
from ..core.events import EventBus
from ..core.models import GameConfig, GameState, SessionState, VaultConfig

# Note: Using SessionState from models.py instead of a separate SessionManager
from ..money.vault import Vault
from ..strategies.base import BaseStrategy


class SimulationEngine:
    """Engine for running dice game simulations."""

    def __init__(
        self,
        vault_config: VaultConfig,
        game_config: GameConfig | None = None,
        event_bus: EventBus | None = None,
        logger=None,
    ):
        """Initialize the simulation engine.

        Args:
            vault_config: Configuration for vault and bankroll
            game_config: Configuration for dice game (uses defaults if None)
            event_bus: Event bus for communication (uses global if None)
            logger: JSONLinesLogger for detailed logging (optional)
        """
        self.vault_config = vault_config
        self.game_config = game_config or GameConfig()
        from ..core.events import event_bus as global_event_bus

        self.event_bus = event_bus or global_event_bus
        self.logger = logger

        # Initialize components
        self.vault = Vault(vault_config)
        self.dice_game = DiceGame(self.game_config)

        # Session tracking
        self.current_session: SessionState | None = None
        self.session_history: list[SessionState] = []

    def run_session(
        self, strategy: BaseStrategy, session_config: dict[str, Any] | None = None
    ) -> SessionState:
        """Run a single simulation session.

        Args:
            strategy: The betting strategy to use
            session_config: Optional session configuration
                - stop_loss: Decimal (ROI threshold for stopping, e.g., -0.1 for -10%)
                - take_profit: Decimal (ROI threshold for stopping, e.g., 0.2 for 20%)
                - max_bets: int (maximum number of bets)
                - max_duration: timedelta (maximum session duration)

        Returns:
            SessionState: Complete session results
        """
        config = session_config or {}

        # Initialize session
        session_id = str(uuid.uuid4())
        initial_balance = self.vault.allocate_session_bankroll()

        game_state = GameState(balance=initial_balance)
        session_state = SessionState(
            game_state=game_state,
            session_id=session_id,
            strategy_name=strategy.get_name(),
            stop_loss=config.get("stop_loss"),
            take_profit=config.get("take_profit"),
            max_bets=config.get("max_bets"),
        )

        self.current_session = session_state
        max_duration = config.get("max_duration")

        # Log session start if logger is available
        if self.logger:
            self.logger.log_session_start(session_state)

        # Run simulation loop
        try:
            while True:
                # Check stop conditions
                should_stop, stop_reason = session_state.should_stop()
                if should_stop:
                    session_state.end_session(stop_reason)
                    break

                # Check duration limit
                if (
                    max_duration
                    and session_state.game_state.session_duration > max_duration.total_seconds()
                ):
                    session_state.end_session("max_duration")
                    break

                # Add current nonce to game state metadata
                if self.dice_game.is_provably_fair_enabled:
                    game_state.metadata["current_nonce"] = (
                        self.dice_game.provably_fair.current_seeds.nonce
                    )

                # Get bet decision from strategy
                decision = strategy.decide_bet(game_state)

                # Log bet decision if logger is available
                if self.logger:
                    self.logger.log_bet_decision(
                        decision, game_state, strategy.get_name(), session_id
                    )

                # Handle non-betting actions (Provably Fair constraint)
                if decision.skip and decision.action:
                    if decision.action == "change_seed":
                        # Rotate seeds (resets nonce to 0)
                        self.dice_game.rotate_seeds()
                        game_state.seed_rotations_count += 1

                        # Log seed change action
                        if self.logger:
                            self.logger.log_strategy_event(
                                "seed_change",
                                strategy.get_name(),
                                session_id,
                                {
                                    "old_nonce": game_state.metadata.get("current_nonce", 0),
                                    "new_server_seed_hash": (
                                        self.dice_game.provably_fair.current_seeds.server_seed_hash
                                    ),
                                    "seed_rotations_count": (game_state.seed_rotations_count),
                                },
                            )

                        # Notify strategy of seed change
                        if hasattr(strategy, "on_seed_change"):
                            strategy.on_seed_change()
                        continue

                    elif decision.action == "toggle_bet_type":
                        # Toggle UNDER/OVER without betting (doesn't consume nonce)
                        game_state.current_bet_type = decision.bet_type
                        game_state.bet_type_toggles += 1

                        # Log bet type toggle action
                        if self.logger:
                            self.logger.log_strategy_event(
                                "bet_type_toggle",
                                strategy.get_name(),
                                session_id,
                                {
                                    "new_bet_type": decision.bet_type.value
                                    if decision.bet_type
                                    else None,
                                    "bet_type_toggles": game_state.bet_type_toggles,
                                },
                            )
                        continue

                    elif decision.action == "forced_parking_bet":
                        # This is a forced bet, continue to normal betting
                        # Log parking bet action
                        if self.logger:
                            self.logger.log_strategy_event(
                                "parking_bet",
                                strategy.get_name(),
                                session_id,
                                {
                                    "reason": "forced_parking_bet",
                                    "amount": str(decision.amount),
                                    "target": strategy.select_target(game_state),
                                    "bet_type": strategy.select_bet_type(game_state).value,
                                },
                            )
                        pass

                # Skip if strategy says to skip (old behavior)
                elif decision.skip:
                    # If strategy can't bet, end session
                    if decision.reason in [
                        "Insufficient balance",
                        "Bet below minimum after limits",
                    ]:
                        session_state.end_session(decision.reason)
                        break
                    continue

                # Execute bet (consumes nonce)
                result = self.dice_game.roll(decision.amount, decision.multiplier)

                # Track parking bets
                if decision.action == "forced_parking_bet":
                    game_state.parking_bets_count += 1
                    if not result.won:
                        game_state.parking_losses += result.amount

                # Update states
                session_state.update(result)
                strategy.update_after_result(result)

                # Log bet result if logger is available
                if self.logger:
                    self.logger.log_bet_result(result, game_state, strategy.get_name(), session_id)

        except Exception as e:
            session_state.end_session(f"error: {str(e)}")

        # Finalize session
        if session_state.ended_at is None:
            session_state.end_session("completed")

        # Update vault with results
        self.vault.return_session_profit(initial_balance, session_state.game_state.balance)

        # Log session end if logger is available
        if self.logger:
            self.logger.log_session_end(session_state)

        # Store session
        self.session_history.append(session_state)
        self.current_session = None

        return session_state

    def run_multiple_sessions(
        self,
        strategy: BaseStrategy,
        num_sessions: int,
        session_config: dict[str, Any] | None = None,
        reset_strategy_between_sessions: bool = True,
        parallel: bool = False,
        max_workers: int | None = None,
    ) -> list[SessionState]:
        """Run multiple simulation sessions.

        Args:
            strategy: The betting strategy to use
            num_sessions: Number of sessions to run
            session_config: Configuration for each session
            reset_strategy_between_sessions: Whether to reset strategy state
                between sessions
            parallel: Whether to run sessions in parallel (faster but uses more memory)
            max_workers: Maximum number of parallel workers (defaults to CPU count)

        Returns:
            List of SessionState results
        """
        if parallel and num_sessions > 10:
            return self._run_sessions_parallel(
                strategy,
                num_sessions,
                session_config,
                reset_strategy_between_sessions,
                max_workers,
            )

        # Sequential execution for small batches or when parallel is disabled
        sessions = []

        for i in range(num_sessions):
            if reset_strategy_between_sessions and i > 0:
                strategy.reset_state()

            session = self.run_session(strategy, session_config)
            sessions.append(session)

            # Stop early if vault is depleted
            if self.vault.can_start_session() is False:
                break

        return sessions

    def _run_sessions_parallel(
        self,
        strategy: BaseStrategy,
        num_sessions: int,
        session_config: dict[str, Any] | None = None,
        reset_strategy_between_sessions: bool = True,
        max_workers: int | None = None,
    ) -> list[SessionState]:
        """Run sessions in parallel for better performance.

        Note: Each process gets its own strategy instance to avoid sharing issues.
        """
        if max_workers is None:
            max_workers = min(cpu_count(), 4)  # Limit to 4 to avoid overwhelming system

        sessions = []

        # Split sessions into batches for better memory management
        batch_size = max(1, num_sessions // max_workers)

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = []

            for batch_start in range(0, num_sessions, batch_size):
                batch_end = min(batch_start + batch_size, num_sessions)
                batch_sessions = batch_end - batch_start

                # Submit batch to worker
                future = executor.submit(
                    _run_session_batch,
                    self.vault_config,
                    self.game_config,
                    strategy,
                    batch_sessions,
                    session_config,
                    reset_strategy_between_sessions,
                )
                futures.append(future)

            # Collect results as they complete
            for future in as_completed(futures):
                try:
                    batch_results = future.result()
                    sessions.extend(batch_results)
                except Exception as e:
                    print(f"Batch failed with error: {e}")

        # Update our vault with final results (simplified)
        for session in sessions:
            initial_balance = session.game_state.session_start_balance
            final_balance = session.game_state.balance
            self.vault.return_session_profit(initial_balance, final_balance)

        # Store in our history
        self.session_history.extend(sessions)

        return sessions[:num_sessions]  # Ensure we don't return more than requested

    def get_simulation_summary(self) -> dict[str, Any]:
        """Get summary statistics for all completed sessions.

        Returns:
            Dictionary with simulation summary statistics
        """
        if not self.session_history:
            return {"total_sessions": 0}

        total_sessions = len(self.session_history)
        total_bets = sum(s.game_state.bets_count for s in self.session_history)
        total_profit = sum(s.game_state.total_profit for s in self.session_history)
        total_wagered = sum(s.game_state.total_wagered for s in self.session_history)

        profitable_sessions = sum(1 for s in self.session_history if s.game_state.total_profit > 0)
        avg_session_duration = (
            sum(s.total_session_time for s in self.session_history) / total_sessions
        )

        # Get stop reasons
        stop_reasons = {}
        for session in self.session_history:
            reason = session.stop_reason or "unknown"
            stop_reasons[reason] = stop_reasons.get(reason, 0) + 1

        # Calculate win rates and ROI
        win_rate = sum(s.game_state.win_rate for s in self.session_history) / total_sessions
        overall_roi = float(total_profit / total_wagered) if total_wagered > 0 else 0.0

        # Drawdown analysis
        max_drawdowns = [s.game_state.max_drawdown for s in self.session_history]
        avg_max_drawdown = sum(max_drawdowns) / len(max_drawdowns)
        worst_drawdown = max(max_drawdowns) if max_drawdowns else Decimal("0")

        return {
            "total_sessions": total_sessions,
            "total_bets": total_bets,
            "total_profit": float(total_profit),
            "total_wagered": float(total_wagered),
            "overall_roi": overall_roi,
            "profitable_sessions": profitable_sessions,
            "profitability_rate": profitable_sessions / total_sessions,
            "average_win_rate": win_rate,
            "average_session_duration": avg_session_duration,
            "stop_reasons": stop_reasons,
            "average_max_drawdown": float(avg_max_drawdown),
            "worst_drawdown": float(worst_drawdown),
            "vault_status": self.vault.get_stats(),
        }

    def reset_engine(self) -> None:
        """Reset the engine to initial state."""
        self.vault = Vault(self.vault_config)
        self.current_session = None
        self.session_history.clear()

    def get_session_by_id(self, session_id: str) -> SessionState | None:
        """Get a session by its ID.

        Args:
            session_id: The session ID to search for

        Returns:
            SessionState if found, None otherwise
        """
        for session in self.session_history:
            if session.session_id == session_id:
                return session
        return None

    def export_sessions_data(self) -> list[dict[str, Any]]:
        """Export all session data for analysis.

        Returns:
            List of dictionaries containing session data
        """
        data = []

        for session in self.session_history:
            session_data = {
                "session_id": session.session_id,
                "strategy_name": session.strategy_name,
                "bot_id": session.bot_id,
                "started_at": session.started_at.isoformat(),
                "ended_at": session.ended_at.isoformat() if session.ended_at else None,
                "stop_reason": session.stop_reason,
                "duration_seconds": session.total_session_time,
                "initial_balance": float(session.game_state.session_start_balance),
                "final_balance": float(session.game_state.balance),
                "total_profit": float(session.game_state.total_profit),
                "total_wagered": float(session.game_state.total_wagered),
                "roi": session.game_state.session_roi,
                "bets_count": session.game_state.bets_count,
                "wins_count": session.game_state.wins_count,
                "losses_count": session.game_state.losses_count,
                "win_rate": session.game_state.win_rate,
                "max_consecutive_wins": session.game_state.max_consecutive_wins,
                "max_consecutive_losses": session.game_state.max_consecutive_losses,
                "max_drawdown": float(session.game_state.max_drawdown),
                "sharpe_ratio": session.game_state.sharpe_ratio,
                "peak_balance": float(session.peak_balance),
                "lowest_balance": float(session.lowest_balance),
                "bets_per_minute": session.game_state.bets_per_minute,
                "stop_loss": float(session.stop_loss) if session.stop_loss else None,
                "take_profit": float(session.take_profit) if session.take_profit else None,
                "max_bets": session.max_bets,
            }
            data.append(session_data)

        return data


def _run_session_batch(
    vault_config: VaultConfig,
    game_config: GameConfig,
    strategy: BaseStrategy,
    num_sessions: int,
    session_config: dict[str, Any] | None = None,
    reset_strategy_between_sessions: bool = True,
) -> list[SessionState]:
    """Helper function to run a batch of sessions in a separate process.

    This function is called by ProcessPoolExecutor and creates its own
    engine instance to avoid sharing state between processes.
    """
    from ..strategies.factory import StrategyFactory

    # Create a fresh engine for this process
    engine = SimulationEngine(vault_config, game_config)

    # Create a fresh strategy instance to avoid sharing state
    strategy_genome = strategy.get_genome()
    strategy_config = {
        "strategy": strategy_genome["strategy_type"].lower(),
        "base_bet": strategy_genome["base_bet"],
        "max_losses": strategy_genome["max_losses"],
        "multiplier": strategy_genome["multiplier"],
        "default_multiplier": strategy_genome["default_multiplier"],
    }

    fresh_strategy = StrategyFactory.create_from_dict(strategy_config)

    # Run the sessions
    sessions = []
    for i in range(num_sessions):
        if reset_strategy_between_sessions and i > 0:
            fresh_strategy.reset_state()

        session = engine.run_session(fresh_strategy, session_config)
        sessions.append(session)

        # Stop early if vault is depleted
        if not engine.vault.can_start_session():
            break

    return sessions
