"""
JSON Lines logger for structured logging of dice game events and results.
"""

import json
import logging
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from ..core.models import BetDecision, BetResult, GameState, SessionState


class LogType:
    """Constants for log type classification."""

    # Simulation types
    SIMULATION_SINGLE = "simulation_single"
    SIMULATION_COMPARISON = "simulation_comparison"
    SIMULATION_PARAMETER_SWEEP = "simulation_parameter_sweep"

    # Strategy types
    STRATEGY_BASIC = "strategy_basic"
    STRATEGY_COMPOSITE = "strategy_composite"
    STRATEGY_ADAPTIVE = "strategy_adaptive"

    # Session types
    SESSION_MANUAL = "session_manual"
    SESSION_AUTOMATED = "session_automated"

    # Analysis types
    ANALYSIS_PERFORMANCE = "analysis_performance"
    ANALYSIS_VALIDATION = "analysis_validation"


def get_log_path(
    base_dir: str | Path, filename: str, log_type: str | None = None
) -> Path:
    """
    Determine the appropriate log path based on filename and log type.

    Args:
        base_dir: Base directory (usually 'betlog')
        filename: Log filename
        log_type: Optional explicit log type

    Returns:
        Complete path for the log file
    """
    base_path = Path(base_dir)

    # If log_type is explicitly provided, use it
    if log_type:
        type_mapping = {
            LogType.SIMULATION_SINGLE: "simulations/single",
            LogType.SIMULATION_COMPARISON: "simulations/comparison",
            LogType.SIMULATION_PARAMETER_SWEEP: "simulations/parameter_sweep",
            LogType.STRATEGY_BASIC: "strategies/basic",
            LogType.STRATEGY_COMPOSITE: "strategies/composite",
            LogType.STRATEGY_ADAPTIVE: "strategies/adaptive",
            LogType.SESSION_MANUAL: "sessions/manual",
            LogType.SESSION_AUTOMATED: "sessions/automated",
            LogType.ANALYSIS_PERFORMANCE: "analysis/performance",
            LogType.ANALYSIS_VALIDATION: "analysis/validation",
        }

        if log_type in type_mapping:
            return base_path / type_mapping[log_type] / filename

    # Auto-detect based on filename patterns
    filename_lower = filename.lower()

    # Strategy classification (high priority)
    if "composite" in filename_lower:
        return base_path / "strategies" / "composite" / filename
    elif "adaptive" in filename_lower:
        return base_path / "strategies" / "adaptive" / filename
    elif any(
        strategy in filename_lower
        for strategy in ["martingale", "fibonacci", "dalembert", "flat", "paroli"]
    ):
        return base_path / "strategies" / "basic" / filename

    # Analysis classification (before session to catch performance/benchmark/validation)
    elif "performance" in filename_lower or "benchmark" in filename_lower:
        return base_path / "analysis" / "performance" / filename
    elif "validation" in filename_lower or "debug" in filename_lower:
        return base_path / "analysis" / "validation" / filename

    # Simulation classification
    elif "comparison" in filename_lower:
        return base_path / "simulations" / "comparison" / filename
    elif "parameter_sweep" in filename_lower or "sweep" in filename_lower:
        return base_path / "simulations" / "parameter_sweep" / filename
    elif "simulation" in filename_lower:
        return base_path / "simulations" / "single" / filename

    # Session classification (lower priority)
    elif "manual" in filename_lower or "test" in filename_lower:
        return base_path / "sessions" / "manual" / filename
    elif "automated" in filename_lower:
        return base_path / "sessions" / "automated" / filename

    # Default fallback to sessions/manual for unclassified logs
    return base_path / "sessions" / "manual" / filename


class JSONLinesLogger:
    """Logger that writes structured data in JSON Lines format."""

    def __init__(
        self,
        log_file: str | Path,
        level: int = logging.INFO,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        log_type: str | None = None,
        base_dir: str | Path = "betlog",
    ):
        """Initialize the JSON Lines logger.

        Args:
            log_file: Path to the log file (can be just filename for
                auto-classification)
            level: Logging level
            max_file_size: Maximum file size before rotation (bytes)
            backup_count: Number of backup files to keep
            log_type: Optional explicit log type for classification
            base_dir: Base directory for organized logs (default: betlog)
        """
        # If log_file is just a filename, use organized path
        if "/" not in str(log_file) and "\\" not in str(log_file):
            self.log_file = get_log_path(base_dir, str(log_file), log_type)
        else:
            self.log_file = Path(log_file)

        self.level = level
        self.max_file_size = max_file_size
        self.backup_count = backup_count

        # Ensure log directory exists
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        # Setup logger
        self.logger = logging.getLogger(f"dicebot.jsonl.{self.log_file.stem}")
        self.logger.setLevel(level)

        # Clear existing handlers
        self.logger.handlers.clear()

        # Add rotating file handler
        from logging.handlers import RotatingFileHandler

        handler = RotatingFileHandler(
            self.log_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding="utf-8",
        )
        handler.setLevel(level)

        # Custom formatter for JSON Lines
        formatter = JSONLinesFormatter()
        handler.setFormatter(formatter)

        self.logger.addHandler(handler)
        self.logger.propagate = False

    def log_bet_decision(
        self,
        decision: BetDecision,
        game_state: GameState,
        strategy_name: str,
        session_id: str,
    ) -> None:
        """Log a bet decision.

        Args:
            decision: The bet decision made
            game_state: Current game state
            strategy_name: Name of the strategy
            session_id: Current session ID
        """
        data = {
            "event_type": "bet_decision",
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "strategy_name": strategy_name,
            "decision": {
                "amount": str(decision.amount),
                "multiplier": decision.multiplier,
                "skip": decision.skip,
                "reason": decision.reason,
                "confidence": decision.confidence,
                "metadata": decision.metadata,
            },
            "game_state": {
                "balance": str(game_state.balance),
                "bets_count": game_state.bets_count,
                "wins_count": game_state.wins_count,
                "losses_count": game_state.losses_count,
                "consecutive_wins": game_state.consecutive_wins,
                "consecutive_losses": game_state.consecutive_losses,
                "total_profit": str(game_state.total_profit),
                "total_wagered": str(game_state.total_wagered),
                "win_rate": game_state.win_rate,
                "roi": game_state.roi,
                "current_drawdown": str(game_state.current_drawdown),
                "max_drawdown": str(game_state.max_drawdown),
            },
        }

        self.logger.info(data)

    def log_bet_result(
        self,
        result: BetResult,
        game_state: GameState,
        strategy_name: str,
        session_id: str,
    ) -> None:
        """Log a bet result.

        Args:
            result: The bet result
            game_state: Updated game state after the bet
            strategy_name: Name of the strategy
            session_id: Current session ID
        """
        data = {
            "event_type": "bet_result",
            "timestamp": result.timestamp.isoformat(),
            "session_id": session_id,
            "strategy_name": strategy_name,
            "result": {
                "roll": result.roll,
                "won": result.won,
                "threshold": result.threshold,
                "amount": str(result.amount),
                "payout": str(result.payout),
                "profit": str(
                    result.payout - result.amount if result.won else -result.amount
                ),
                "bet_type": result.bet_type.value if result.bet_type else None,
                "target": result.target,
                "multiplier": result.multiplier,
            },
            "provably_fair": {
                "server_seed_hash": result.server_seed_hash,
                "client_seed": result.client_seed,
                "nonce": result.nonce,
                "verification_data": result.to_verification_dict()
                if hasattr(result, "to_verification_dict")
                else None,
            },
            "game_state_after": {
                "balance": str(game_state.balance),
                "bets_count": game_state.bets_count,
                "wins_count": game_state.wins_count,
                "losses_count": game_state.losses_count,
                "consecutive_wins": game_state.consecutive_wins,
                "consecutive_losses": game_state.consecutive_losses,
                "total_profit": str(game_state.total_profit),
                "total_wagered": str(game_state.total_wagered),
                "win_rate": game_state.win_rate,
                "roi": game_state.roi,
                "current_drawdown": str(game_state.current_drawdown),
                "max_drawdown": str(game_state.max_drawdown),
            },
        }

        self.logger.info(data)

    def log_session_start(self, session_state: SessionState) -> None:
        """Log session start.

        Args:
            session_state: The session state at start
        """
        data = {
            "event_type": "session_start",
            "timestamp": session_state.started_at.isoformat(),
            "session_id": session_state.session_id,
            "bot_id": session_state.bot_id,
            "strategy_name": session_state.strategy_name,
            "initial_balance": str(session_state.game_state.session_start_balance),
            "session_config": {
                "stop_loss": str(session_state.stop_loss)
                if session_state.stop_loss
                else None,
                "take_profit": str(session_state.take_profit)
                if session_state.take_profit
                else None,
                "max_bets": session_state.max_bets,
            },
        }

        self.logger.info(data)

    def log_session_end(self, session_state: SessionState) -> None:
        """Log session end.

        Args:
            session_state: The session state at end
        """
        data = {
            "event_type": "session_end",
            "timestamp": session_state.ended_at.isoformat()
            if session_state.ended_at
            else datetime.now().isoformat(),
            "session_id": session_state.session_id,
            "bot_id": session_state.bot_id,
            "strategy_name": session_state.strategy_name,
            "stop_reason": session_state.stop_reason,
            "duration_seconds": session_state.total_session_time,
            "session_summary": {
                "initial_balance": str(session_state.game_state.session_start_balance),
                "final_balance": str(session_state.game_state.balance),
                "total_profit": str(session_state.game_state.total_profit),
                "total_wagered": str(session_state.game_state.total_wagered),
                "roi": session_state.game_state.session_roi,
                "bets_count": session_state.game_state.bets_count,
                "wins_count": session_state.game_state.wins_count,
                "losses_count": session_state.game_state.losses_count,
                "win_rate": session_state.game_state.win_rate,
                "max_consecutive_wins": session_state.game_state.max_consecutive_wins,
                "max_consecutive_losses": (
                    session_state.game_state.max_consecutive_losses
                ),
                "max_drawdown": str(session_state.game_state.max_drawdown),
                "sharpe_ratio": session_state.game_state.sharpe_ratio,
                "peak_balance": str(session_state.peak_balance),
                "lowest_balance": str(session_state.lowest_balance),
                "bets_per_minute": session_state.game_state.bets_per_minute,
            },
        }

        self.logger.info(data)

    def log_strategy_event(
        self, event_type: str, strategy_name: str, session_id: str, data: dict[str, Any]
    ) -> None:
        """Log a strategy-specific event.

        Args:
            event_type: Type of strategy event
            strategy_name: Name of the strategy
            session_id: Current session ID
            data: Additional event data
        """
        log_data = {
            "event_type": f"strategy_{event_type}",
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "strategy_name": strategy_name,
            "data": data,
        }

        self.logger.info(log_data)

    def log_streak_event(
        self,
        streak_type: str,
        streak_length: int,
        strategy_name: str,
        session_id: str,
        game_state: GameState,
    ) -> None:
        """Log a winning or losing streak event.

        Args:
            streak_type: 'win' or 'loss'
            streak_length: Length of the streak
            strategy_name: Name of the strategy
            session_id: Current session ID
            game_state: Current game state
        """
        data = {
            "event_type": f"{streak_type}_streak",
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "strategy_name": strategy_name,
            "streak": {
                "type": streak_type,
                "length": streak_length,
                "current_balance": str(game_state.balance),
                "current_drawdown": str(game_state.current_drawdown),
                "total_profit": str(game_state.total_profit),
            },
        }

        self.logger.info(data)

    def log_error(
        self,
        error: Exception,
        context: str,
        session_id: str | None = None,
        strategy_name: str | None = None,
    ) -> None:
        """Log an error event.

        Args:
            error: The exception that occurred
            context: Context where the error occurred
            session_id: Current session ID (if applicable)
            strategy_name: Strategy name (if applicable)
        """
        data = {
            "event_type": "error",
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "strategy_name": strategy_name,
            "error": {
                "type": type(error).__name__,
                "message": str(error),
                "context": context,
            },
        }

        self.logger.error(data)

    def log_simulation_summary(
        self, summary: dict[str, Any], strategy_name: str, num_sessions: int
    ) -> None:
        """Log simulation summary.

        Args:
            summary: Simulation summary data
            strategy_name: Name of the strategy
            num_sessions: Number of sessions run
        """
        data = {
            "event_type": "simulation_summary",
            "timestamp": datetime.now().isoformat(),
            "strategy_name": strategy_name,
            "num_sessions": num_sessions,
            "summary": summary,
        }

        self.logger.info(data)

    def close(self) -> None:
        """Close the logger and all handlers."""
        for handler in self.logger.handlers:
            handler.close()
        self.logger.handlers.clear()


class JSONLinesFormatter(logging.Formatter):
    """Custom formatter for JSON Lines output."""

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as JSON.

        Args:
            record: The log record to format

        Returns:
            JSON string representation of the record
        """
        if isinstance(record.msg, dict):
            # Record message is already a dict
            log_data = record.msg.copy()
        else:
            # Convert string message to dict
            log_data = {
                "event_type": "log_message",
                "timestamp": datetime.now().isoformat(),
                "level": record.levelname,
                "message": record.getMessage(),
            }

        # Add standard logging fields if not present
        if "level" not in log_data:
            log_data["level"] = record.levelname

        # Serialize to JSON
        return json.dumps(log_data, default=self._json_serializer, ensure_ascii=False)

    def _json_serializer(self, obj: Any) -> Any:
        """Custom JSON serializer for special types.

        Args:
            obj: Object to serialize

        Returns:
            Serializable representation of the object
        """
        if isinstance(obj, Decimal):
            return str(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, "__dict__"):
            return obj.__dict__
        else:
            return str(obj)


class LogAnalyzer:
    """Analyzer for JSON Lines log files."""

    def __init__(self, log_file: str | Path):
        """Initialize the log analyzer.

        Args:
            log_file: Path to the log file to analyze
        """
        self.log_file = Path(log_file)

    def read_events(self, event_type: str | None = None) -> list[dict]:
        """Read events from the log file.

        Args:
            event_type: Filter by event type (optional)

        Returns:
            List of event dictionaries
        """
        events = []

        try:
            with open(self.log_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        event = json.loads(line)
                        if event_type is None or event.get("event_type") == event_type:
                            events.append(event)
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            pass

        return events

    def get_session_events(self, session_id: str) -> list[dict]:
        """Get all events for a specific session.

        Args:
            session_id: The session ID to filter by

        Returns:
            List of events for the session
        """
        events = []

        try:
            with open(self.log_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        event = json.loads(line)
                        if event.get("session_id") == session_id:
                            events.append(event)
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            pass

        return events

    def analyze_session_performance(self, session_id: str) -> dict[str, Any]:
        """Analyze performance for a specific session.

        Args:
            session_id: The session ID to analyze

        Returns:
            Dictionary with session analysis
        """
        events = self.get_session_events(session_id)

        if not events:
            return {"error": "No events found for session"}

        bet_results = [e for e in events if e.get("event_type") == "bet_result"]
        session_start = next(
            (e for e in events if e.get("event_type") == "session_start"), None
        )
        session_end = next(
            (e for e in events if e.get("event_type") == "session_end"), None
        )

        if not bet_results:
            return {"error": "No bet results found for session"}

        # Calculate metrics
        total_bets = len(bet_results)
        wins = sum(1 for r in bet_results if r["result"]["won"])
        total_profit = sum(Decimal(r["result"]["profit"]) for r in bet_results)
        total_wagered = sum(Decimal(r["result"]["amount"]) for r in bet_results)

        analysis = {
            "session_id": session_id,
            "strategy_name": bet_results[0].get("strategy_name"),
            "total_bets": total_bets,
            "wins": wins,
            "losses": total_bets - wins,
            "win_rate": wins / total_bets if total_bets > 0 else 0,
            "total_profit": float(total_profit),
            "total_wagered": float(total_wagered),
            "roi": float(total_profit / total_wagered) if total_wagered > 0 else 0,
            "session_start": session_start["timestamp"] if session_start else None,
            "session_end": session_end["timestamp"] if session_end else None,
            "stop_reason": session_end.get("stop_reason") if session_end else None,
        }

        return analysis
