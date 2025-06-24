"""
Performance monitoring and alerting for DiceBot.
"""

import logging
import threading
import time
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any

import psutil
import schedule

from ..core.models import SessionState


class PerformanceMonitor:
    """Monitor DiceBot performance and send alerts."""

    def __init__(
        self,
        alert_callback: Callable[[str, str, str], None] | None = None,
        check_interval: int = 60,
    ):
        """Initialize performance monitor.

        Args:
            alert_callback: Function to call for alerts (alert_type, message, severity)
            check_interval: Check interval in seconds
        """
        self.alert_callback = alert_callback
        self.check_interval = check_interval
        self.logger = logging.getLogger(__name__)

        # Monitoring data
        self.session_stats: dict[str, SessionState] = {}
        self.system_alerts: list[dict[str, Any]] = []
        self.performance_history: list[dict[str, Any]] = []

        # Alert thresholds
        self.thresholds = {
            "cpu_warning": 80.0,
            "cpu_critical": 95.0,
            "memory_warning": 85.0,
            "memory_critical": 95.0,
            "disk_warning": 90.0,
            "disk_critical": 98.0,
            "loss_streak_warning": 10,
            "loss_streak_critical": 20,
            "drawdown_warning": 0.20,  # 20%
            "drawdown_critical": 0.50,  # 50%
        }

        # Monitoring state
        self._running = False
        self._monitor_thread: threading.Thread | None = None

        # Schedule system checks
        schedule.every(self.check_interval).seconds.do(self.check_system_performance)

    def start_monitoring(self) -> None:
        """Start performance monitoring."""
        if self._running:
            return

        self._running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

        self.logger.info("Performance monitoring started")
        self._send_alert("info", "Performance monitoring started", "info")

    def stop_monitoring(self) -> None:
        """Stop performance monitoring."""
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)

        self.logger.info("Performance monitoring stopped")

    def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while self._running:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")
                time.sleep(5)

    def register_session(self, session_state: SessionState) -> None:
        """Register a session for monitoring.

        Args:
            session_state: Session to monitor
        """
        self.session_stats[session_state.session_id] = session_state
        self.logger.info(
            f"Registered session for monitoring: {session_state.session_id}"
        )

    def update_session(self, session_state: SessionState) -> None:
        """Update session state and check for alerts.

        Args:
            session_state: Updated session state
        """
        self.session_stats[session_state.session_id] = session_state
        self._check_session_alerts(session_state)

    def unregister_session(self, session_id: str) -> None:
        """Unregister a session from monitoring.

        Args:
            session_id: Session ID to remove
        """
        if session_id in self.session_stats:
            del self.session_stats[session_id]
            self.logger.info(f"Unregistered session: {session_id}")

    def check_system_performance(self) -> None:
        """Check system performance metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent >= self.thresholds["cpu_critical"]:
                self._send_alert(
                    "error", f"Critical CPU usage: {cpu_percent:.1f}%", "critical"
                )
            elif cpu_percent >= self.thresholds["cpu_warning"]:
                self._send_alert(
                    "warning", f"High CPU usage: {cpu_percent:.1f}%", "warning"
                )

            # Memory usage
            memory = psutil.virtual_memory()
            if memory.percent >= self.thresholds["memory_critical"]:
                self._send_alert(
                    "error", f"Critical memory usage: {memory.percent:.1f}%", "critical"
                )
            elif memory.percent >= self.thresholds["memory_warning"]:
                self._send_alert(
                    "warning", f"High memory usage: {memory.percent:.1f}%", "warning"
                )

            # Disk usage
            disk = psutil.disk_usage("/")
            if disk.percent >= self.thresholds["disk_critical"]:
                self._send_alert(
                    "error", f"Critical disk usage: {disk.percent:.1f}%", "critical"
                )
            elif disk.percent >= self.thresholds["disk_warning"]:
                self._send_alert(
                    "warning", f"High disk usage: {disk.percent:.1f}%", "warning"
                )

            # Store performance data
            self.performance_history.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "disk_percent": disk.percent,
                    "active_sessions": len(self.session_stats),
                }
            )

            # Keep only last 24 hours of data
            cutoff = datetime.now() - timedelta(hours=24)
            self.performance_history = [
                p
                for p in self.performance_history
                if datetime.fromisoformat(p["timestamp"]) > cutoff
            ]

        except Exception as e:
            self.logger.error(f"System performance check failed: {e}")

    def _check_session_alerts(self, session_state: SessionState) -> None:
        """Check session-specific alerts.

        Args:
            session_state: Session state to check
        """
        game_state = session_state.game_state

        # Loss streak alerts
        if game_state.consecutive_losses >= self.thresholds["loss_streak_critical"]:
            self._send_alert(
                "error",
                f"Critical loss streak: {game_state.consecutive_losses} losses in session {session_state.session_id}",
                "critical",
            )
        elif game_state.consecutive_losses >= self.thresholds["loss_streak_warning"]:
            self._send_alert(
                "warning",
                f"Warning loss streak: {game_state.consecutive_losses} losses in session {session_state.session_id}",
                "warning",
            )

        # Drawdown alerts
        current_drawdown = float(game_state.current_drawdown)
        if current_drawdown >= self.thresholds["drawdown_critical"]:
            self._send_alert(
                "error",
                f"Critical drawdown: {current_drawdown:.1%} in session {session_state.session_id}",
                "critical",
            )
        elif current_drawdown >= self.thresholds["drawdown_warning"]:
            self._send_alert(
                "warning",
                f"Warning drawdown: {current_drawdown:.1%} in session {session_state.session_id}",
                "warning",
            )

        # Profit milestones (positive alerts)
        profit_percent = float(game_state.session_roi) / 100
        if profit_percent >= 0.50:  # 50% profit
            self._send_alert(
                "success",
                f"Exceptional profit: {profit_percent:.1%} ROI in session {session_state.session_id}",
                "info",
            )
        elif profit_percent >= 0.20:  # 20% profit
            self._send_alert(
                "success",
                f"Good profit: {profit_percent:.1%} ROI in session {session_state.session_id}",
                "info",
            )

    def _send_alert(self, alert_type: str, message: str, severity: str) -> None:
        """Send alert notification.

        Args:
            alert_type: Type of alert
            message: Alert message
            severity: Alert severity level
        """
        alert = {
            "timestamp": datetime.now().isoformat(),
            "type": alert_type,
            "message": message,
            "severity": severity,
        }

        self.system_alerts.append(alert)

        # Keep only last 100 alerts
        if len(self.system_alerts) > 100:
            self.system_alerts = self.system_alerts[-100:]

        self.logger.warning(f"Alert [{severity}]: {message}")

        # Call external alert callback if provided
        if self.alert_callback:
            try:
                self.alert_callback(alert_type, message, severity)
            except Exception as e:
                self.logger.error(f"Alert callback failed: {e}")

    def get_performance_summary(self) -> dict[str, Any]:
        """Get performance monitoring summary.

        Returns:
            Dictionary with performance data
        """
        try:
            # Current system stats
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            # Session stats
            active_sessions = len(self.session_stats)
            total_profit = sum(
                float(session.game_state.total_profit)
                for session in self.session_stats.values()
            )

            # Recent alerts
            recent_alerts = list(self.system_alerts[-10:])

            return {
                "timestamp": datetime.now().isoformat(),
                "system": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "disk_percent": disk.percent,
                },
                "sessions": {
                    "active_count": active_sessions,
                    "total_profit": total_profit,
                },
                "alerts": {
                    "total_count": len(self.system_alerts),
                    "recent": recent_alerts,
                },
                "monitoring": {
                    "running": self._running,
                    "check_interval": self.check_interval,
                },
            }

        except Exception as e:
            self.logger.error(f"Performance summary failed: {e}")
            return {"error": str(e)}

    def set_threshold(self, metric: str, value: float) -> bool:
        """Set alert threshold.

        Args:
            metric: Metric name
            value: Threshold value

        Returns:
            True if successful
        """
        if metric in self.thresholds:
            old_value = self.thresholds[metric]
            self.thresholds[metric] = value

            self.logger.info(f"Updated threshold {metric}: {old_value} -> {value}")
            self._send_alert("info", f"Threshold updated: {metric} = {value}", "info")
            return True
        else:
            self.logger.warning(f"Unknown threshold metric: {metric}")
            return False
