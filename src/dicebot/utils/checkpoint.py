"""
Checkpoint and recovery system for DiceBot simulations.
"""

import json
import pickle
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from ..core.models import SessionState
from .progress import progress_manager


class CheckpointManager:
    """Manages simulation checkpoints for recovery."""

    def __init__(self, checkpoint_dir: Path | str = "checkpoints"):
        """Initialize checkpoint manager.

        Args:
            checkpoint_dir: Directory to store checkpoint files
        """
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(exist_ok=True)

        # Cleanup old checkpoints on init
        self._cleanup_old_checkpoints()

    def create_checkpoint(
        self,
        simulation_id: str,
        completed_sessions: list[SessionState],
        remaining_sessions: int,
        strategy_config: dict[str, Any],
        session_config: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Path:
        """Create a checkpoint file.

        Args:
            simulation_id: Unique identifier for the simulation
            completed_sessions: List of completed sessions
            remaining_sessions: Number of sessions still to run
            strategy_config: Strategy configuration
            session_config: Session configuration
            metadata: Additional metadata

        Returns:
            Path to the created checkpoint file
        """
        checkpoint_data = {
            "timestamp": datetime.now().isoformat(),
            "simulation_id": simulation_id,
            "completed_sessions_count": len(completed_sessions),
            "remaining_sessions": remaining_sessions,
            "strategy_config": strategy_config,
            "session_config": session_config,
            "metadata": metadata or {},
            "version": "1.0",
        }

        # Save summary in JSON for easy inspection
        summary_file = self.checkpoint_dir / f"{simulation_id}_summary.json"
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(checkpoint_data, f, indent=2, default=str)

        # Save full data in pickle for exact recovery
        data_file = self.checkpoint_dir / f"{simulation_id}_data.pkl"
        full_data = {**checkpoint_data, "completed_sessions": completed_sessions}

        with open(data_file, "wb") as f:
            pickle.dump(full_data, f, protocol=pickle.HIGHEST_PROTOCOL)

        progress_manager.print_info(f"Checkpoint saved: {summary_file.name}")
        return summary_file

    def load_checkpoint(self, simulation_id: str) -> dict[str, Any] | None:
        """Load a checkpoint by simulation ID.

        Args:
            simulation_id: Simulation identifier

        Returns:
            Checkpoint data or None if not found
        """
        data_file = self.checkpoint_dir / f"{simulation_id}_data.pkl"

        if not data_file.exists():
            return None

        try:
            with open(data_file, "rb") as f:
                return pickle.load(f)
        except Exception as e:
            progress_manager.print_error(f"Failed to load checkpoint {simulation_id}: {e}")
            return None

    def list_checkpoints(self) -> list[dict[str, Any]]:
        """List all available checkpoints.

        Returns:
            List of checkpoint summaries
        """
        checkpoints = []

        for summary_file in self.checkpoint_dir.glob("*_summary.json"):
            try:
                with open(summary_file, encoding="utf-8") as f:
                    summary = json.load(f)

                # Add file info
                summary["file_size"] = summary_file.stat().st_size
                summary["file_age_hours"] = (time.time() - summary_file.stat().st_mtime) / 3600

                checkpoints.append(summary)

            except Exception as e:
                progress_manager.print_warning(f"Failed to read checkpoint {summary_file}: {e}")

        # Sort by timestamp (newest first)
        checkpoints.sort(key=lambda x: x["timestamp"], reverse=True)
        return checkpoints

    def delete_checkpoint(self, simulation_id: str) -> bool:
        """Delete a checkpoint.

        Args:
            simulation_id: Simulation identifier

        Returns:
            True if deleted successfully
        """
        summary_file = self.checkpoint_dir / f"{simulation_id}_summary.json"
        data_file = self.checkpoint_dir / f"{simulation_id}_data.pkl"

        deleted = False

        if summary_file.exists():
            summary_file.unlink()
            deleted = True

        if data_file.exists():
            data_file.unlink()
            deleted = True

        if deleted:
            progress_manager.print_info(f"Checkpoint {simulation_id} deleted")

        return deleted

    def _cleanup_old_checkpoints(self, max_age_days: int = 7):
        """Clean up checkpoints older than max_age_days.

        Args:
            max_age_days: Maximum age in days
        """
        max_age_seconds = max_age_days * 24 * 3600
        current_time = time.time()

        cleaned_count = 0

        for checkpoint_file in self.checkpoint_dir.glob("*"):
            if checkpoint_file.is_file():
                age = current_time - checkpoint_file.stat().st_mtime
                if age > max_age_seconds:
                    checkpoint_file.unlink()
                    cleaned_count += 1

        if cleaned_count > 0:
            progress_manager.print_info(f"Cleaned up {cleaned_count} old checkpoint files")

    def get_recovery_suggestions(self) -> list[str]:
        """Get suggestions for recovery based on available checkpoints.

        Returns:
            List of recovery suggestion strings
        """
        checkpoints = self.list_checkpoints()
        suggestions = []

        if not checkpoints:
            return ["No checkpoints available for recovery"]

        # Find recent incomplete simulations
        recent_incomplete = [
            cp
            for cp in checkpoints
            if cp.get("remaining_sessions", 0) > 0 and cp["file_age_hours"] < 24
        ]

        if recent_incomplete:
            suggestions.append("Recent incomplete simulations found:")
            for cp in recent_incomplete[:3]:  # Show top 3
                strategy = cp["strategy_config"].get("strategy", "unknown")
                remaining = cp.get("remaining_sessions", 0)
                suggestions.append(
                    f"  • {cp['simulation_id']}: {strategy} strategy, "
                    f"{remaining} sessions remaining"
                )

        return suggestions


class AutoCheckpoint:
    """Context manager for automatic checkpointing during simulations."""

    def __init__(
        self,
        simulation_id: str,
        strategy_config: dict[str, Any],
        session_config: dict[str, Any] | None = None,
        checkpoint_interval: int = 100,
        checkpoint_manager: CheckpointManager | None = None,
    ):
        """Initialize auto-checkpoint context.

        Args:
            simulation_id: Unique simulation identifier
            strategy_config: Strategy configuration
            session_config: Session configuration
            checkpoint_interval: Sessions between checkpoints
            checkpoint_manager: Checkpoint manager instance
        """
        self.simulation_id = simulation_id
        self.strategy_config = strategy_config
        self.session_config = session_config
        self.checkpoint_interval = checkpoint_interval
        self.checkpoint_manager = checkpoint_manager or CheckpointManager()

        self.completed_sessions: list[SessionState] = []
        self.total_sessions = 0
        self.last_checkpoint_count = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Save final checkpoint if simulation completed normally
        if exc_type is None and self.completed_sessions:
            self.checkpoint_manager.create_checkpoint(
                f"{self.simulation_id}_final",
                self.completed_sessions,
                0,  # No remaining sessions
                self.strategy_config,
                self.session_config,
                {"status": "completed", "total_sessions": len(self.completed_sessions)},
            )

    def add_session(self, session: SessionState):
        """Add a completed session and checkpoint if needed.

        Args:
            session: Completed session
        """
        self.completed_sessions.append(session)

        # Check if we need to checkpoint
        if (len(self.completed_sessions) - self.last_checkpoint_count) >= self.checkpoint_interval:
            remaining = max(0, self.total_sessions - len(self.completed_sessions))

            self.checkpoint_manager.create_checkpoint(
                self.simulation_id,
                self.completed_sessions,
                remaining,
                self.strategy_config,
                self.session_config,
                {
                    "status": "in_progress",
                    "progress": len(self.completed_sessions) / max(1, self.total_sessions),
                },
            )

            self.last_checkpoint_count = len(self.completed_sessions)

    def set_total_sessions(self, total: int):
        """Set the total number of sessions expected.

        Args:
            total: Total number of sessions
        """
        self.total_sessions = total


# Global checkpoint manager instance
checkpoint_manager = CheckpointManager()
