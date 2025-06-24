"""
Advanced metrics calculator for analyzing dice game performance and strategies.
"""

from datetime import timedelta
from decimal import Decimal
from typing import Any

import numpy as np
from scipy import stats

from ..core.models import BetResult, SessionState


class PerformanceMetrics:
    """Calculator for advanced performance metrics."""

    @staticmethod
    def calculate_sharpe_ratio(
        returns: list[float], risk_free_rate: float = 0.0, periods_per_year: int = 365
    ) -> float:
        """Calculate Sharpe ratio.

        Args:
            returns: List of returns (profit/loss per bet as ratio)
            risk_free_rate: Risk-free rate (annualized)
            periods_per_year: Number of periods per year for annualization

        Returns:
            Sharpe ratio
        """
        if len(returns) < 2:
            return 0.0

        returns_array = np.array(returns)
        excess_returns = returns_array - (risk_free_rate / periods_per_year)

        if np.std(excess_returns) == 0:
            return 0.0

        sharpe = np.mean(excess_returns) / np.std(excess_returns)
        return sharpe * np.sqrt(periods_per_year)

    @staticmethod
    def calculate_sortino_ratio(
        returns: list[float], target_return: float = 0.0, periods_per_year: int = 365
    ) -> float:
        """Calculate Sortino ratio (only penalizes downside volatility).

        Args:
            returns: List of returns
            target_return: Target return rate
            periods_per_year: Number of periods per year

        Returns:
            Sortino ratio
        """
        if len(returns) < 2:
            return 0.0

        returns_array = np.array(returns)
        excess_returns = returns_array - target_return
        downside_returns = excess_returns[excess_returns < 0]

        if len(downside_returns) == 0:
            return float("inf") if np.mean(excess_returns) > 0 else 0.0

        downside_deviation = np.sqrt(np.mean(downside_returns**2))

        if downside_deviation == 0:
            return 0.0

        return np.mean(excess_returns) / downside_deviation * np.sqrt(periods_per_year)

    @staticmethod
    def calculate_calmar_ratio(
        total_return: float,
        max_drawdown: float,
        periods: int,
        periods_per_year: int = 365,
    ) -> float:
        """Calculate Calmar ratio (annualized return / max drawdown).

        Args:
            total_return: Total return over the period
            max_drawdown: Maximum drawdown (as positive percentage)
            periods: Number of periods
            periods_per_year: Periods per year for annualization

        Returns:
            Calmar ratio
        """
        if max_drawdown == 0:
            return float("inf") if total_return > 0 else 0.0

        annualized_return = (1 + total_return) ** (periods_per_year / periods) - 1
        return annualized_return / max_drawdown

    @staticmethod
    def calculate_value_at_risk(
        returns: list[float], confidence_level: float = 0.05
    ) -> float:
        """Calculate Value at Risk (VaR).

        Args:
            returns: List of returns
            confidence_level: Confidence level (e.g., 0.05 for 95% VaR)

        Returns:
            Value at Risk
        """
        if not returns:
            return 0.0

        return np.percentile(returns, confidence_level * 100)

    @staticmethod
    def calculate_expected_shortfall(
        returns: list[float], confidence_level: float = 0.05
    ) -> float:
        """Calculate Expected Shortfall (Conditional VaR).

        Args:
            returns: List of returns
            confidence_level: Confidence level

        Returns:
            Expected Shortfall
        """
        if not returns:
            return 0.0

        var = PerformanceMetrics.calculate_value_at_risk(returns, confidence_level)
        returns_array = np.array(returns)
        tail_returns = returns_array[returns_array <= var]

        if len(tail_returns) == 0:
            return var

        return np.mean(tail_returns)

    @staticmethod
    def calculate_maximum_drawdown_duration(
        bet_history: list[BetResult],
    ) -> tuple[int, timedelta]:
        """Calculate maximum drawdown duration.

        Args:
            bet_history: List of bet results

        Returns:
            Tuple of (number of bets, time duration) for max drawdown
        """
        if not bet_history:
            return 0, timedelta(0)

        balance = Decimal("0")
        peak_balance = Decimal("0")
        max_dd_bets = 0
        max_dd_duration = timedelta(0)
        current_dd_start_bet = 0
        current_dd_start_time = None
        in_drawdown = False

        for i, bet in enumerate(bet_history):
            if bet.won:
                profit = bet.payout - bet.amount
            else:
                profit = -bet.amount

            balance += profit

            if balance > peak_balance:
                # New peak, end of drawdown
                if in_drawdown and current_dd_start_time:
                    dd_bets = i - current_dd_start_bet
                    dd_duration = bet.timestamp - current_dd_start_time

                    if dd_bets > max_dd_bets:
                        max_dd_bets = dd_bets
                    if dd_duration > max_dd_duration:
                        max_dd_duration = dd_duration

                peak_balance = balance
                in_drawdown = False
                current_dd_start_bet = i
                current_dd_start_time = bet.timestamp
            else:
                # In drawdown
                if not in_drawdown:
                    in_drawdown = True
                    current_dd_start_bet = i
                    current_dd_start_time = bet.timestamp

        # Check final drawdown if still ongoing
        if in_drawdown and current_dd_start_time and bet_history:
            final_dd_bets = len(bet_history) - current_dd_start_bet
            final_dd_duration = bet_history[-1].timestamp - current_dd_start_time

            if final_dd_bets > max_dd_bets:
                max_dd_bets = final_dd_bets
            if final_dd_duration > max_dd_duration:
                max_dd_duration = final_dd_duration

        return max_dd_bets, max_dd_duration

    @staticmethod
    def calculate_profit_factor(bet_history: list[BetResult]) -> float:
        """Calculate profit factor (gross profit / gross loss).

        Args:
            bet_history: List of bet results

        Returns:
            Profit factor
        """
        if not bet_history:
            return 0.0

        gross_profit = Decimal("0")
        gross_loss = Decimal("0")

        for bet in bet_history:
            if bet.won:
                gross_profit += bet.payout - bet.amount
            else:
                gross_loss += bet.amount

        if gross_loss == 0:
            return float("inf") if gross_profit > 0 else 0.0

        return float(gross_profit / gross_loss)

    @staticmethod
    def calculate_kelly_criterion(
        win_probability: float, win_payout_ratio: float, loss_ratio: float = 1.0
    ) -> float:
        """Calculate optimal bet size using Kelly criterion.

        Args:
            win_probability: Probability of winning (0-1)
            win_payout_ratio: Payout ratio for wins (e.g., 2.0 for 2x)
            loss_ratio: Loss ratio (typically 1.0)

        Returns:
            Optimal fraction of bankroll to bet
        """
        if win_probability <= 0 or win_probability >= 1:
            return 0.0

        loss_probability = 1 - win_probability
        numerator = win_probability * win_payout_ratio - loss_probability * loss_ratio
        kelly_fraction = numerator / win_payout_ratio

        return max(0.0, kelly_fraction)


class SessionAnalyzer:
    """Analyzer for individual session performance."""

    def __init__(self, session_state: SessionState):
        """Initialize with a session state.

        Args:
            session_state: The session to analyze
        """
        self.session = session_state
        self.game_state = session_state.game_state

    def get_basic_metrics(self) -> dict[str, Any]:
        """Get basic session metrics.

        Returns:
            Dictionary of basic metrics
        """
        return {
            "session_id": self.session.session_id,
            "strategy_name": self.session.strategy_name,
            "duration_seconds": self.session.total_session_time,
            "duration_minutes": self.session.total_session_time / 60,
            "bets_count": self.game_state.bets_count,
            "wins_count": self.game_state.wins_count,
            "losses_count": self.game_state.losses_count,
            "win_rate": self.game_state.win_rate,
            "total_profit": float(self.game_state.total_profit),
            "total_wagered": float(self.game_state.total_wagered),
            "roi": self.game_state.roi,
            "session_roi": self.game_state.session_roi,
            "max_consecutive_wins": self.game_state.max_consecutive_wins,
            "max_consecutive_losses": self.game_state.max_consecutive_losses,
            "max_drawdown": float(self.game_state.max_drawdown),
            "current_drawdown": float(self.game_state.current_drawdown),
            "sharpe_ratio": self.game_state.sharpe_ratio,
            "bets_per_minute": self.game_state.bets_per_minute,
            "initial_balance": float(self.game_state.session_start_balance),
            "final_balance": float(self.game_state.balance),
            "peak_balance": float(self.session.peak_balance),
            "lowest_balance": float(self.session.lowest_balance),
            "stop_reason": self.session.stop_reason,
        }

    def get_advanced_metrics(self) -> dict[str, Any]:
        """Get advanced session metrics.

        Returns:
            Dictionary of advanced metrics
        """
        if not self.game_state.bet_history:
            return {"error": "No bet history available"}

        # Calculate returns
        returns = []
        for bet in self.game_state.bet_history:
            if bet.won:
                profit = bet.payout - bet.amount
            else:
                profit = -bet.amount
            returns.append(float(profit / bet.amount))

        # Advanced metrics
        sortino = PerformanceMetrics.calculate_sortino_ratio(returns)
        calmar = PerformanceMetrics.calculate_calmar_ratio(
            self.game_state.session_roi,
            float(self.game_state.max_drawdown),
            len(returns),
        )
        var_95 = PerformanceMetrics.calculate_value_at_risk(returns, 0.05)
        expected_shortfall = PerformanceMetrics.calculate_expected_shortfall(
            returns, 0.05
        )
        profit_factor = PerformanceMetrics.calculate_profit_factor(
            self.game_state.bet_history
        )

        # Drawdown duration
        max_dd_results = PerformanceMetrics.calculate_maximum_drawdown_duration(
            self.game_state.bet_history
        )
        max_dd_bets, max_dd_duration = max_dd_results

        return {
            "advanced_ratios": {
                "sortino_ratio": sortino,
                "calmar_ratio": calmar,
                "profit_factor": profit_factor,
            },
            "risk_metrics": {
                "value_at_risk_95": var_95,
                "expected_shortfall_95": expected_shortfall,
                "max_drawdown_bets": max_dd_bets,
                "max_drawdown_duration_seconds": max_dd_duration.total_seconds(),
                "max_drawdown_duration_minutes": max_dd_duration.total_seconds() / 60,
            },
            "bet_analysis": {
                "average_bet_size": (
                    float(self.game_state.total_wagered / self.game_state.bets_count)
                    if self.game_state.bets_count > 0
                    else 0
                ),
                "largest_bet": float(
                    max(bet.amount for bet in self.game_state.bet_history)
                ),
                "smallest_bet": float(
                    min(bet.amount for bet in self.game_state.bet_history)
                ),
                "average_win_payout": (
                    float(
                        np.mean(
                            [
                                bet.payout
                                for bet in self.game_state.bet_history
                                if bet.won
                            ]
                        )
                    )
                    if any(bet.won for bet in self.game_state.bet_history)
                    else 0
                ),
                "largest_single_loss": (
                    float(
                        max(
                            bet.amount
                            for bet in self.game_state.bet_history
                            if not bet.won
                        )
                    )
                    if any(not bet.won for bet in self.game_state.bet_history)
                    else 0
                ),
                "largest_single_win": (
                    float(
                        max(
                            bet.payout - bet.amount
                            for bet in self.game_state.bet_history
                            if bet.won
                        )
                    )
                    if any(bet.won for bet in self.game_state.bet_history)
                    else 0
                ),
            },
            "returns_analysis": {
                "mean_return": np.mean(returns) if returns else 0,
                "std_return": np.std(returns) if returns else 0,
                "skewness": float(stats.skew(returns)) if len(returns) > 2 else 0,
                "kurtosis": float(stats.kurtosis(returns)) if len(returns) > 3 else 0,
                "min_return": min(returns) if returns else 0,
                "max_return": max(returns) if returns else 0,
            },
        }

    def get_time_series_analysis(self) -> dict[str, Any]:
        """Get time series analysis of the session.

        Returns:
            Dictionary with time series metrics
        """
        if not self.game_state.bet_history:
            return {"error": "No bet history available"}

        # Calculate cumulative metrics over time
        cumulative_profit = []
        cumulative_bets = []
        rolling_win_rate = []
        balance_history = []

        current_profit = Decimal("0")
        current_balance = self.game_state.session_start_balance
        window_size = min(20, len(self.game_state.bet_history))  # 20-bet rolling window

        for i, bet in enumerate(self.game_state.bet_history):
            if bet.won:
                profit = bet.payout - bet.amount
                current_balance += profit
            else:
                profit = -bet.amount
                current_balance -= bet.amount

            current_profit += profit
            cumulative_profit.append(float(current_profit))
            cumulative_bets.append(i + 1)
            balance_history.append(float(current_balance))

            # Rolling win rate
            if i >= window_size - 1:
                window_start = max(0, i - window_size + 1)
                window_wins = sum(
                    1
                    for b in self.game_state.bet_history[window_start : i + 1]
                    if b.won
                )
                rolling_win_rate.append(window_wins / window_size)
            else:
                window_wins = sum(
                    1 for b in self.game_state.bet_history[: i + 1] if b.won
                )
                rolling_win_rate.append(window_wins / (i + 1))

        return {
            "time_series": {
                "cumulative_profit": cumulative_profit,
                "cumulative_bets": cumulative_bets,
                "balance_history": balance_history,
                "rolling_win_rate": rolling_win_rate,
                "timestamps": [
                    bet.timestamp.isoformat() for bet in self.game_state.bet_history
                ],
            },
            "trend_analysis": {
                "profit_trend_slope": self._calculate_trend_slope(cumulative_profit),
                "balance_volatility": np.std(balance_history) if balance_history else 0,
                "win_rate_stability": np.std(rolling_win_rate)
                if rolling_win_rate
                else 0,
            },
        }

    def _calculate_trend_slope(self, values: list[float]) -> float:
        """Calculate trend slope using linear regression.

        Args:
            values: List of values

        Returns:
            Slope of the trend line
        """
        if len(values) < 2:
            return 0.0

        x = np.arange(len(values))
        slope, _, _, _, _ = stats.linregress(x, values)
        return float(slope)


class MultiSessionAnalyzer:
    """Analyzer for multiple sessions (strategy comparison)."""

    def __init__(self, sessions: list[SessionState]):
        """Initialize with list of sessions.

        Args:
            sessions: List of session states to analyze
        """
        self.sessions = sessions

    def get_aggregate_metrics(self) -> dict[str, Any]:
        """Get aggregate metrics across all sessions.

        Returns:
            Dictionary of aggregate metrics
        """
        if not self.sessions:
            return {"error": "No sessions provided"}

        total_bets = sum(s.game_state.bets_count for s in self.sessions)
        total_wins = sum(s.game_state.wins_count for s in self.sessions)
        total_profit = sum(s.game_state.total_profit for s in self.sessions)
        total_wagered = sum(s.game_state.total_wagered for s in self.sessions)
        total_duration = sum(s.total_session_time for s in self.sessions)

        profitable_sessions = sum(
            1 for s in self.sessions if s.game_state.total_profit > 0
        )

        # Session-level metrics
        session_profits = [float(s.game_state.total_profit) for s in self.sessions]
        session_rois = [s.game_state.session_roi for s in self.sessions]
        session_durations = [s.total_session_time for s in self.sessions]

        return {
            "aggregate_performance": {
                "total_sessions": len(self.sessions),
                "total_bets": total_bets,
                "total_wins": total_wins,
                "total_losses": total_bets - total_wins,
                "overall_win_rate": total_wins / total_bets if total_bets > 0 else 0,
                "total_profit": float(total_profit),
                "total_wagered": float(total_wagered),
                "overall_roi": float(total_profit / total_wagered)
                if total_wagered > 0
                else 0,
                "total_duration_hours": total_duration / 3600,
                "average_bets_per_session": total_bets / len(self.sessions),
                "profitable_sessions": profitable_sessions,
                "profitability_rate": profitable_sessions / len(self.sessions),
            },
            "session_statistics": {
                "average_session_profit": np.mean(session_profits),
                "median_session_profit": np.median(session_profits),
                "std_session_profit": np.std(session_profits),
                "best_session_profit": max(session_profits),
                "worst_session_profit": min(session_profits),
                "average_session_roi": np.mean(session_rois),
                "median_session_roi": np.median(session_rois),
                "std_session_roi": np.std(session_rois),
                "average_session_duration_minutes": np.mean(session_durations) / 60,
                "median_session_duration_minutes": np.median(session_durations) / 60,
            },
            "risk_analysis": {
                "profit_volatility": np.std(session_profits),
                "roi_volatility": np.std(session_rois),
                "max_session_drawdown": max(
                    float(s.game_state.max_drawdown) for s in self.sessions
                ),
                "average_session_drawdown": np.mean(
                    [float(s.game_state.max_drawdown) for s in self.sessions]
                ),
                "sessions_with_significant_loss": sum(
                    1 for s in self.sessions if s.game_state.session_roi < -0.1
                ),
                "worst_consecutive_losses": max(
                    s.game_state.max_consecutive_losses for s in self.sessions
                ),
            },
        }

    def compare_strategies(
        self, strategy_groups: dict[str, list[SessionState]]
    ) -> dict[str, Any]:
        """Compare performance between different strategies.

        Args:
            strategy_groups: Dictionary mapping strategy names to session lists

        Returns:
            Strategy comparison analysis
        """
        if not strategy_groups:
            return {"error": "No strategy groups provided"}

        strategy_metrics = {}

        for strategy_name, sessions in strategy_groups.items():
            if not sessions:
                continue

            analyzer = MultiSessionAnalyzer(sessions)
            metrics = analyzer.get_aggregate_metrics()
            strategy_metrics[strategy_name] = metrics

        # Ranking and comparison
        rankings = self._create_strategy_rankings(strategy_metrics)

        return {
            "strategy_metrics": strategy_metrics,
            "rankings": rankings,
            "comparison_summary": self._generate_comparison_summary(
                strategy_metrics, rankings
            ),
        }

    def _create_strategy_rankings(
        self, strategy_metrics: dict[str, dict]
    ) -> dict[str, list]:
        """Create rankings for different metrics.

        Args:
            strategy_metrics: Metrics for each strategy

        Returns:
            Rankings by different criteria
        """
        strategies = list(strategy_metrics.keys())

        rankings = {
            "by_total_profit": sorted(
                strategies,
                key=lambda s: strategy_metrics[s]["aggregate_performance"][
                    "total_profit"
                ],
                reverse=True,
            ),
            "by_roi": sorted(
                strategies,
                key=lambda s: strategy_metrics[s]["aggregate_performance"][
                    "overall_roi"
                ],
                reverse=True,
            ),
            "by_profitability_rate": sorted(
                strategies,
                key=lambda s: strategy_metrics[s]["aggregate_performance"][
                    "profitability_rate"
                ],
                reverse=True,
            ),
            "by_win_rate": sorted(
                strategies,
                key=lambda s: strategy_metrics[s]["aggregate_performance"][
                    "overall_win_rate"
                ],
                reverse=True,
            ),
            "by_risk_adjusted": sorted(
                strategies,
                key=lambda s: strategy_metrics[s]["aggregate_performance"][
                    "overall_roi"
                ]
                / max(0.01, strategy_metrics[s]["risk_analysis"]["roi_volatility"]),
                reverse=True,
            ),
        }

        return rankings

    def _generate_comparison_summary(
        self, strategy_metrics: dict, rankings: dict
    ) -> dict[str, Any]:
        """Generate comparison summary and recommendations.

        Args:
            strategy_metrics: Metrics for each strategy
            rankings: Rankings by different criteria

        Returns:
            Comparison summary
        """
        best_overall = rankings["by_roi"][0] if rankings["by_roi"] else None
        most_consistent = (
            rankings["by_profitability_rate"][0]
            if rankings["by_profitability_rate"]
            else None
        )
        lowest_risk = (
            min(
                strategy_metrics.keys(),
                key=lambda s: strategy_metrics[s]["risk_analysis"]["roi_volatility"],
            )
            if strategy_metrics
            else None
        )

        return {
            "best_overall_performer": best_overall,
            "most_consistent_performer": most_consistent,
            "lowest_risk_performer": lowest_risk,
            "recommendations": [
                f"Best ROI: {best_overall}"
                if best_overall
                else "No strategies analyzed",
                f"Most consistent: {most_consistent}"
                if most_consistent
                else "No strategies analyzed",
                f"Lowest risk: {lowest_risk}"
                if lowest_risk
                else "No strategies analyzed",
            ],
        }
