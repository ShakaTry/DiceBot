"""
High-level simulation runner for orchestrating multiple strategies and comparisons.
"""

import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from ..core.models import GameConfig, VaultConfig
from ..strategies.factory import StrategyFactory
from ..utils.logger import JSONLinesLogger
from ..utils.progress import progress_manager
from .engine import SimulationEngine


class SimulationRunner:
    """High-level runner for orchestrating simulations."""

    def __init__(
        self,
        total_capital: Decimal,
        output_dir: str | Path | None = None,
        game_config: GameConfig | None = None,
    ):
        """Initialize the simulation runner.

        Args:
            total_capital: Total capital to use for simulations
            output_dir: Directory to save results (defaults to 'results/')
            game_config: Game configuration (uses defaults if None)
        """
        self.total_capital = total_capital
        self.output_dir = Path(output_dir) if output_dir else Path("results")
        self.game_config = game_config or GameConfig()

        # Ensure output directory exists
        self.output_dir.mkdir(exist_ok=True)

        # Results storage
        self.simulation_results: dict[str, dict[str, Any]] = {}
        self.comparison_results: dict[str, Any] = {}

    def run_strategy_simulation(
        self,
        strategy_config: dict[str, Any],
        num_sessions: int = 100,
        session_config: dict[str, Any] | None = None,
        save_results: bool = True,
        parallel: bool = None,
        max_workers: int | None = None,
        show_progress: bool = True,
        enable_detailed_logs: bool = False,
        log_dir: str | Path = "logs",
    ) -> dict[str, Any]:
        """Run simulation for a single strategy.

        Args:
            strategy_config: Strategy configuration dict
            num_sessions: Number of sessions to run
            session_config: Session configuration
            save_results: Whether to save results to file
            parallel: Whether to use parallel processing (auto-detect if None)
            max_workers: Maximum number of parallel workers
            show_progress: Whether to show progress bar
            enable_detailed_logs: Whether to enable detailed JSON Lines logging
            log_dir: Directory for detailed log files

        Returns:
            Dictionary with simulation results
        """
        # Auto-enable parallel for large simulations
        if parallel is None:
            parallel = num_sessions >= 50
        # Create strategy
        # Use copy to avoid modifying original
        strategy = StrategyFactory.create_from_dict(strategy_config.copy())
        strategy_name = strategy.get_name()

        # Create vault config
        vault_config = VaultConfig(total_capital=self.total_capital)

        # Create logger if detailed logging is enabled
        logger = None
        if enable_detailed_logs:
            # Create unique log file name with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_filename = f"simulation_{strategy_name}_{timestamp}.jsonl"

            # Import LogType for classification
            from ..utils.logger import LogType

            # Determine log type based on strategy
            log_type = None
            if "composite" in strategy_name.lower():
                log_type = LogType.STRATEGY_COMPOSITE
            elif "adaptive" in strategy_name.lower():
                log_type = LogType.STRATEGY_ADAPTIVE
            elif any(
                basic in strategy_name.lower()
                for basic in ["martingale", "fibonacci", "dalembert", "flat", "paroli"]
            ):
                log_type = LogType.STRATEGY_BASIC
            else:
                log_type = LogType.SIMULATION_SINGLE

            logger = JSONLinesLogger(log_filename, log_type=log_type, base_dir=log_dir)

        # Create and run simulation
        engine = SimulationEngine(vault_config, self.game_config, logger=logger)

        if show_progress:
            description = f"Running {strategy_name} strategy"
            with progress_manager.progress.track_simulation(
                description, num_sessions, show_stats=True
            ) as (task_id, update_fn):
                if parallel:
                    # For parallel execution, we can't track individual sessions
                    sessions = engine.run_multiple_sessions(
                        strategy,
                        num_sessions,
                        session_config,
                        parallel=parallel,
                        max_workers=max_workers,
                    )
                    update_fn(advance=num_sessions)  # Update all at once
                else:
                    # For sequential execution, track each session
                    sessions = []
                    for i in range(num_sessions):
                        if i > 0:
                            strategy.reset_state()
                        session = engine.run_session(strategy, session_config)
                        sessions.append(session)
                        update_fn(session, advance=1)

                        if not engine.vault.can_start_session():
                            break
        else:
            sessions = engine.run_multiple_sessions(
                strategy,
                num_sessions,
                session_config,
                parallel=parallel,
                max_workers=max_workers,
            )

        # Get summary
        summary = engine.get_simulation_summary()

        # Add strategy-specific metrics
        strategy_metrics = {
            "strategy_config": strategy_config,
            "strategy_genome": strategy.get_genome(),
            "strategy_fitness": strategy.calculate_fitness(),
            "strategy_metrics": {
                "total_bets": strategy.metrics.total_bets,
                "win_rate": strategy.metrics.win_rate,
                "roi": strategy.metrics.roi,
                "max_bet_reached": float(strategy.metrics.max_bet_reached),
                "max_consecutive_losses": strategy.metrics.max_consecutive_losses,
                "average_confidence": strategy.metrics.average_confidence,
                "profit_factor": strategy.metrics.profit_factor,
            },
        }

        # Combine results
        results = {
            "simulation_summary": summary,
            "strategy_info": strategy_metrics,
            "sessions_data": engine.export_sessions_data(),
            "simulation_metadata": {
                "run_timestamp": datetime.now().isoformat(),
                "num_sessions_requested": num_sessions,
                "num_sessions_completed": len(sessions),
                "session_config": session_config or {},
                "total_capital": float(self.total_capital),
            },
        }

        # Store results
        self.simulation_results[strategy_name] = results

        # Save to file if requested
        if save_results:
            self._save_strategy_results(strategy_name, results)

        # Close logger if it was created
        if logger:
            logger.close()

        return results

    def run_strategy_comparison(
        self,
        strategy_configs: list[dict[str, Any]],
        num_sessions: int = 100,
        session_config: dict[str, Any] | None = None,
        save_results: bool = True,
        enable_detailed_logs: bool = False,
        log_dir: str | Path = "betlog",
    ) -> dict[str, Any]:
        """Run and compare multiple strategies.

        Args:
            strategy_configs: List of strategy configuration dicts
            num_sessions: Number of sessions per strategy
            session_config: Session configuration
            save_results: Whether to save results to file
            enable_detailed_logs: Whether to enable detailed JSON Lines logging
            log_dir: Directory for detailed log files

        Returns:
            Dictionary with comparison results
        """
        comparison_results = {}
        strategy_summaries = {}

        # Run simulation for each strategy
        for config in strategy_configs:
            try:
                strategy = StrategyFactory.create_from_dict(
                    config.copy()
                )  # Use copy to avoid modifying original
                strategy_name = strategy.get_name()

                # Run simulation with comparison logging if enabled
                results = self.run_strategy_simulation(
                    config,
                    num_sessions,
                    session_config,
                    save_results=False,
                    enable_detailed_logs=enable_detailed_logs,
                    log_dir=log_dir,
                )

                comparison_results[strategy_name] = results
                strategy_summaries[strategy_name] = results["simulation_summary"]

            except Exception as e:
                print(
                    f"Error running strategy {config.get('strategy', 'unknown')}: {e}"
                )
                continue

        # Generate comparison analysis
        analysis = self._analyze_strategy_comparison(strategy_summaries)

        # Combine results
        final_results = {
            "comparison_analysis": analysis,
            "individual_results": comparison_results,
            "metadata": {
                "comparison_timestamp": datetime.now().isoformat(),
                "strategies_compared": len(strategy_configs),
                "num_sessions_per_strategy": num_sessions,
                "session_config": session_config or {},
                "total_capital": float(self.total_capital),
            },
        }

        # Store and save
        self.comparison_results = final_results

        if save_results:
            self._save_comparison_results(final_results)

        return final_results

    def run_parameter_sweep(
        self,
        base_strategy_config: dict[str, Any],
        parameter_ranges: dict[str, list[Any]],
        num_sessions: int = 50,
        session_config: dict[str, Any] | None = None,
        save_results: bool = True,
        enable_detailed_logs: bool = False,
        log_dir: str | Path = "betlog",
    ) -> dict[str, Any]:
        """Run parameter sweep for strategy optimization.

        Args:
            base_strategy_config: Base strategy configuration
            parameter_ranges: Dict of parameter names to lists of values to test
            num_sessions: Number of sessions per parameter combination
            session_config: Session configuration
            save_results: Whether to save results
            enable_detailed_logs: Whether to enable detailed JSON Lines logging
            log_dir: Directory for detailed log files

        Returns:
            Dictionary with sweep results
        """
        sweep_results = []

        # Generate all parameter combinations
        param_combinations = self._generate_parameter_combinations(parameter_ranges)

        for i, params in enumerate(param_combinations):
            # Create config for this combination
            config = base_strategy_config.copy()
            config.update(params)

            try:
                # Run simulation with parameter sweep logging if enabled
                results = self.run_strategy_simulation(
                    config,
                    num_sessions,
                    session_config,
                    save_results=False,
                    enable_detailed_logs=enable_detailed_logs,
                    log_dir=log_dir,
                )

                # Extract key metrics
                summary = results["simulation_summary"]
                sweep_result = {
                    "parameter_combination": params,
                    "roi": summary["overall_roi"],
                    "profitability_rate": summary["profitability_rate"],
                    "average_win_rate": summary["average_win_rate"],
                    "worst_drawdown": summary["worst_drawdown"],
                    "total_sessions": summary["total_sessions"],
                    "strategy_fitness": results["strategy_info"]["strategy_fitness"],
                }

                sweep_results.append(sweep_result)

                # Progress indicator
                print(
                    f"Completed parameter combination {i + 1}/{len(param_combinations)}"
                )

            except Exception as e:
                print(f"Error with parameter combination {params}: {e}")
                continue

        # Analyze results
        best_result = (
            max(sweep_results, key=lambda x: x["strategy_fitness"])
            if sweep_results
            else None
        )

        final_results = {
            "sweep_results": sweep_results,
            "best_parameters": best_result["parameter_combination"]
            if best_result
            else None,
            "best_performance": best_result if best_result else None,
            "parameter_ranges": parameter_ranges,
            "metadata": {
                "sweep_timestamp": datetime.now().isoformat(),
                "base_strategy": base_strategy_config,
                "combinations_tested": len(sweep_results),
                "combinations_requested": len(param_combinations),
                "num_sessions_per_combination": num_sessions,
            },
        }

        if save_results:
            self._save_sweep_results(final_results)

        return final_results

    def _analyze_strategy_comparison(
        self, summaries: dict[str, dict]
    ) -> dict[str, Any]:
        """Analyze comparison results between strategies."""
        if not summaries:
            return {}

        # Ranking by different metrics
        rankings = {
            "by_roi": sorted(
                summaries.items(), key=lambda x: x[1]["overall_roi"], reverse=True
            ),
            "by_profitability_rate": sorted(
                summaries.items(),
                key=lambda x: x[1]["profitability_rate"],
                reverse=True,
            ),
            "by_win_rate": sorted(
                summaries.items(), key=lambda x: x[1]["average_win_rate"], reverse=True
            ),
            "by_drawdown": sorted(
                summaries.items(), key=lambda x: x[1]["worst_drawdown"]
            ),  # Lower is better
        }

        # Calculate statistics
        roi_values = [s["overall_roi"] for s in summaries.values()]
        prof_rates = [s["profitability_rate"] for s in summaries.values()]

        analysis = {
            "rankings": rankings,
            "statistics": {
                "average_roi": sum(roi_values) / len(roi_values),
                "best_roi": max(roi_values),
                "worst_roi": min(roi_values),
                "average_profitability_rate": sum(prof_rates) / len(prof_rates),
                "strategies_with_positive_roi": sum(1 for roi in roi_values if roi > 0),
                "total_strategies": len(summaries),
            },
            "recommendations": self._generate_strategy_recommendations(rankings),
        }

        return analysis

    def _generate_strategy_recommendations(self, rankings: dict) -> list[str]:
        """Generate strategy recommendations based on rankings."""
        recommendations = []

        # Best overall performer
        if rankings["by_roi"]:
            best_roi = rankings["by_roi"][0]
            recommendations.append(
                f"Best ROI: {best_roi[0]} ({best_roi[1]['overall_roi']:.2%})"
            )

        # Most consistent
        if rankings["by_profitability_rate"]:
            best_prof = rankings["by_profitability_rate"][0]
            recommendations.append(
                f"Most consistent: {best_prof[0]} "
                f"({best_prof[1]['profitability_rate']:.1%} profitable sessions)"
            )

        # Lowest risk
        if rankings["by_drawdown"]:
            lowest_dd = rankings["by_drawdown"][0]
            recommendations.append(
                f"Lowest risk: {lowest_dd[0]} "
                f"({lowest_dd[1]['worst_drawdown']:.1%} max drawdown)"
            )

        return recommendations

    def _generate_parameter_combinations(
        self, parameter_ranges: dict[str, list]
    ) -> list[dict]:
        """Generate all combinations of parameters."""
        import itertools

        keys = list(parameter_ranges.keys())
        values = list(parameter_ranges.values())

        combinations = []
        for combo in itertools.product(*values):
            combinations.append(dict(zip(keys, combo, strict=False)))

        return combinations

    def _save_strategy_results(self, strategy_name: str, results: dict) -> None:
        """Save strategy results to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"strategy_{strategy_name}_{timestamp}.json"
        filepath = self.output_dir / filename

        with open(filepath, "w") as f:
            json.dump(results, f, indent=2, default=str)

        print(f"Strategy results saved to: {filepath}")

    def _save_comparison_results(self, results: dict) -> None:
        """Save comparison results to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"strategy_comparison_{timestamp}.json"
        filepath = self.output_dir / filename

        with open(filepath, "w") as f:
            json.dump(results, f, indent=2, default=str)

        print(f"Comparison results saved to: {filepath}")

    def _save_sweep_results(self, results: dict) -> None:
        """Save parameter sweep results to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"parameter_sweep_{timestamp}.json"
        filepath = self.output_dir / filename

        with open(filepath, "w") as f:
            json.dump(results, f, indent=2, default=str)

        print(f"Parameter sweep results saved to: {filepath}")

    def get_latest_results(self) -> dict[str, Any]:
        """Get the most recent simulation results."""
        return {
            "strategy_results": self.simulation_results,
            "comparison_results": self.comparison_results,
        }

    def load_results_from_file(self, filepath: str | Path) -> dict[str, Any]:
        """Load results from a JSON file."""
        with open(filepath) as f:
            return json.load(f)

    def list_saved_results(self) -> list[str]:
        """List all saved result files."""
        json_files = list(self.output_dir.glob("*.json"))
        return [str(f.name) for f in json_files]
