"""
Progress tracking utilities for DiceBot simulations.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)


class SimulationProgress:
    """Enhanced progress tracking for simulations."""

    def __init__(self, console: Console | None = None):
        self.console = console or Console()
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=self.console,
            refresh_per_second=10,
        )

    @contextmanager
    def track_simulation(
        self, description: str, total_sessions: int, show_stats: bool = True
    ) -> Iterator[tuple[TaskID, callable]]:
        """Context manager for tracking simulation progress.

        Args:
            description: Description of the simulation
            total_sessions: Total number of sessions to run
            show_stats: Whether to show live statistics

        Yields:
            Tuple of (task_id, update_function)
        """
        with self.progress:
            task_id = self.progress.add_task(description, total=total_sessions)

            # Statistics tracking
            stats = {
                "profitable_sessions": 0,
                "total_profit": 0.0,
                "avg_roi": 0.0,
                "sessions_completed": 0,
            }

            def update_progress(session_result: Any = None, advance: int = 1):
                """Update progress and optionally show live stats."""
                self.progress.advance(task_id, advance)

                if session_result and show_stats:
                    # Update statistics
                    stats["sessions_completed"] += 1
                    if hasattr(session_result, "game_state"):
                        profit = float(session_result.game_state.total_profit)
                        stats["total_profit"] += profit
                        if profit > 0:
                            stats["profitable_sessions"] += 1

                        # Update running average ROI
                        roi = session_result.game_state.session_roi
                        stats["avg_roi"] = (
                            stats["avg_roi"] * (stats["sessions_completed"] - 1) + roi
                        ) / stats["sessions_completed"]

                    # Update task description with live stats
                    profitable_rate = (
                        stats["profitable_sessions"] / stats["sessions_completed"] * 100
                        if stats["sessions_completed"] > 0
                        else 0
                    )

                    new_description = (
                        f"{description} | "
                        f"Profit: {stats['total_profit']:.4f} LTC | "
                        f"Profitable: {profitable_rate:.1f}% | "
                        f"Avg ROI: {stats['avg_roi']:.2%}"
                    )
                    self.progress.update(task_id, description=new_description)

            yield task_id, update_progress

    @contextmanager
    def track_comparison(
        self, strategies: list[str], sessions_per_strategy: int
    ) -> Iterator[tuple[TaskID, callable]]:
        """Track strategy comparison progress.

        Args:
            strategies: List of strategy names
            sessions_per_strategy: Number of sessions per strategy

        Yields:
            Tuple of (task_id, update_function)
        """
        total_sessions = len(strategies) * sessions_per_strategy
        description = f"Comparing {len(strategies)} strategies"

        with self.progress:
            task_id = self.progress.add_task(description, total=total_sessions)

            current_strategy = ""
            strategy_index = 0

            def update_comparison(
                strategy_name: str = None, session_result: Any = None, advance: int = 1
            ):
                nonlocal current_strategy, strategy_index

                if strategy_name and strategy_name != current_strategy:
                    current_strategy = strategy_name
                    strategy_index += 1

                self.progress.advance(task_id, advance)

                # Update description with current strategy
                new_description = (
                    f"Comparing strategies ({strategy_index}/{len(strategies)}) | "
                    f"Current: {current_strategy}"
                )
                self.progress.update(task_id, description=new_description)

            yield task_id, update_comparison


class ProgressManager:
    """Global progress manager for DiceBot operations."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.console = Console()
            cls._instance.simulation_progress = SimulationProgress(cls._instance.console)
        return cls._instance

    @property
    def progress(self) -> SimulationProgress:
        return self.simulation_progress

    def print(self, *args, **kwargs):
        """Print message to console (compatible with rich formatting)."""
        self.console.print(*args, **kwargs)

    def print_warning(self, message: str):
        """Print warning message."""
        self.console.print(f"⚠️  [yellow]Warning:[/yellow] {message}")

    def print_error(self, message: str):
        """Print error message."""
        self.console.print(f"❌ [red]Error:[/red] {message}")

    def print_success(self, message: str):
        """Print success message."""
        self.console.print(f"✅ [green]Success:[/green] {message}")

    def print_info(self, message: str):
        """Print info message."""
        self.console.print(f"ℹ️  [blue]Info:[/blue] {message}")


# Global progress manager instance
progress_manager = ProgressManager()
