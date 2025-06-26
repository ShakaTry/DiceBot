"""Interface for ``python -m DiceBot``."""

import json
import sys
from argparse import ArgumentParser, Namespace
from collections.abc import Sequence
from decimal import Decimal
from typing import Any

from . import __version__

__all__ = ["main"]


def main(args: Sequence[str] | None = None) -> None:
    """Argument parser for the CLI."""
    parser = ArgumentParser(
        prog="DiceBot",
        description="DiceBot - Artificial Consciousness Evolution Laboratory",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=__version__,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Simulate command
    sim_parser = subparsers.add_parser("simulate", help="Run dice game simulations")
    sim_parser.add_argument(
        "--capital",
        type=str,
        required=True,
        help="Total capital (e.g., '250' or '1000.50')",
    )
    sim_parser.add_argument(
        "--strategy",
        type=str,
        required=True,
        help="Strategy name (e.g., 'martingale', 'fibonacci')",
    )
    sim_parser.add_argument(
        "--sessions", type=int, help="Number of sessions to run (default: from config)"
    )
    sim_parser.add_argument(
        "--preset",
        type=str,
        help="Use strategy preset (conservative, moderate, aggressive, experimental)",
    )
    sim_parser.add_argument("--base-bet", type=str, help="Base bet amount (overrides preset)")
    sim_parser.add_argument(
        "--max-losses", type=int, help="Maximum consecutive losses (overrides preset)"
    )
    sim_parser.add_argument(
        "--multiplier",
        type=float,
        help="Bet multiplier for applicable strategies (overrides preset)",
    )
    sim_parser.add_argument(
        "--stop-loss",
        type=float,
        help="Stop loss threshold (ROI, e.g., -0.1 for -10%%)",
    )
    sim_parser.add_argument(
        "--take-profit",
        type=float,
        help="Take profit threshold (ROI, e.g., 0.2 for 20%%)",
    )
    sim_parser.add_argument("--max-bets", type=int, help="Maximum bets per session")
    sim_parser.add_argument(
        "--output-dir",
        type=str,
        default="results",
        help="Output directory (default: results)",
    )
    sim_parser.add_argument("--quiet", "-q", action="store_true", help="Reduce output verbosity")
    sim_parser.add_argument("--no-progress", action="store_true", help="Disable progress bar")
    sim_parser.add_argument("--parallel", action="store_true", help="Force parallel execution")
    sim_parser.add_argument(
        "--detailed-logs",
        action="store_true",
        help="Enable detailed JSON Lines logging for each bet",
    )
    sim_parser.add_argument(
        "--log-dir",
        type=str,
        default="betlog",
        help="Directory for detailed logs (default: betlog)",
    )
    sim_parser.add_argument(
        "--slack-webhook",
        type=str,
        help="Slack webhook URL for notifications",
    )
    sim_parser.add_argument(
        "--enable-monitoring",
        action="store_true",
        help="Enable performance monitoring and alerts",
    )

    # Compare command
    comp_parser = subparsers.add_parser("compare", help="Compare multiple strategies")
    comp_parser.add_argument("--capital", type=str, required=True, help="Total capital")
    comp_parser.add_argument(
        "--strategies",
        type=str,
        nargs="+",
        required=True,
        help="Strategy names to compare",
    )
    comp_parser.add_argument(
        "--sessions", type=int, default=100, help="Number of sessions per strategy"
    )
    comp_parser.add_argument("--base-bet", type=str, help="Base bet amount")
    comp_parser.add_argument("--output-dir", type=str, default="results", help="Output directory")
    comp_parser.add_argument("--quiet", "-q", action="store_true", help="Reduce output verbosity")
    comp_parser.add_argument("--no-progress", action="store_true", help="Disable progress bar")
    comp_parser.add_argument("--parallel", action="store_true", help="Force parallel execution")

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze simulation results")
    analyze_parser.add_argument("file", type=str, help="Results file to analyze")
    analyze_parser.add_argument(
        "--detailed", "-d", action="store_true", help="Show detailed analysis"
    )

    # Recovery commands
    recovery_parser = subparsers.add_parser("recovery", help="Checkpoint and recovery management")
    recovery_subparsers = recovery_parser.add_subparsers(
        dest="recovery_command", help="Recovery commands"
    )

    # List checkpoints
    recovery_subparsers.add_parser("list", help="List available checkpoints")

    # Resume simulation
    resume_parser = recovery_subparsers.add_parser(
        "resume", help="Resume simulation from checkpoint"
    )
    resume_parser.add_argument("simulation_id", type=str, help="Simulation ID to resume")
    resume_parser.add_argument("--no-progress", action="store_true", help="Disable progress bar")

    # Clean checkpoints
    clean_parser = recovery_subparsers.add_parser("clean", help="Clean old checkpoints")
    clean_parser.add_argument(
        "--max-age", type=int, default=7, help="Maximum age in days (default: 7)"
    )

    # Monitor command
    monitor_parser = subparsers.add_parser("monitor", help="Real-time monitoring and control")
    monitor_parser.add_argument(
        "--slack-webhook",
        type=str,
        help="Slack webhook URL for notifications",
    )
    monitor_parser.add_argument(
        "--check-interval",
        type=int,
        default=60,
        help="Check interval in seconds (default: 60)",
    )
    monitor_parser.add_argument(
        "--cpu-warning",
        type=float,
        default=80.0,
        help="CPU warning threshold percent (default: 80)",
    )
    monitor_parser.add_argument(
        "--memory-warning",
        type=float,
        default=85.0,
        help="Memory warning threshold percent (default: 85)",
    )

    # Parse arguments
    parsed_args = parser.parse_args(args)

    if not parsed_args.command:
        parser.print_help()
        return

    # Import here to avoid circular imports and improve startup time

    try:
        if parsed_args.command == "simulate":
            run_simulate_command(parsed_args)
        elif parsed_args.command == "compare":
            run_compare_command(parsed_args)
        elif parsed_args.command == "analyze":
            run_analyze_command(parsed_args)
        elif parsed_args.command == "recovery":
            run_recovery_command(parsed_args)
        elif parsed_args.command == "monitor":
            run_monitor_command(parsed_args)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def run_simulate_command(args: Namespace) -> None:
    """Run simulation command."""
    from dicebot.simulation.runner import SimulationRunner
    from dicebot.utils.config import DiceBotConfig, get_config
    from dicebot.utils.progress import progress_manager
    from dicebot.utils.validation import ParameterValidator, validate_and_suggest

    # Load configuration
    config: DiceBotConfig = get_config()

    # Validate and parse capital
    try:
        capital: Decimal = ParameterValidator.validate_capital(args.capital)
    except Exception as e:
        progress_manager.print_error(str(e))
        return

    # Build strategy config starting with preset if specified
    strategy_config: dict[str, Any] = {"strategy": args.strategy}

    if args.preset:
        try:
            preset_config: dict[str, Any] = config.get_strategy_preset(args.preset)
            strategy_config.update(preset_config)

            if not args.quiet:
                progress_manager.print_info(f"Using '{args.preset}' preset")
        except KeyError as e:
            progress_manager.print_error(str(e))
            return

    # Override with explicit parameters
    if args.base_bet:
        strategy_config["base_bet"] = args.base_bet
    if args.max_losses:
        strategy_config["max_losses"] = args.max_losses
    if args.multiplier:
        strategy_config["multiplier"] = args.multiplier

    # Set default values from config if not specified
    if "base_bet" not in strategy_config:
        strategy_config["base_bet"] = "0.001"  # Default fallback

    # Build session config
    session_config: dict[str, Any] = {}
    if args.stop_loss:
        session_config["stop_loss"] = Decimal(str(args.stop_loss))
    if args.take_profit:
        session_config["take_profit"] = Decimal(str(args.take_profit))
    if args.max_bets:
        session_config["max_bets"] = args.max_bets

    # Get sessions count from args or config
    sessions: int = args.sessions or config.simulation["default_sessions"]

    # Validate configuration
    if not validate_and_suggest(
        strategy_config, capital, session_config, show_output=not args.quiet
    ):
        return  # Validation failed

    # Setup Slack notifications if webhook provided
    slack_notifier: Any = None  # SlackNotifier type
    if args.slack_webhook:
        from dicebot.integrations.slack_bot import SlackNotifier

        slack_notifier = SlackNotifier(args.slack_webhook)
        if not args.quiet:
            progress_manager.print_info("✅ Slack notifications enabled")

    # Setup monitoring if enabled
    monitor: Any = None  # PerformanceMonitor type
    if args.enable_monitoring:
        from dicebot.integrations.monitoring import PerformanceMonitor

        def alert_callback(alert_type: str, message: str, severity: str) -> None:
            if slack_notifier:
                slack_notifier.notify_alert(alert_type, message)

        monitor = PerformanceMonitor(alert_callback=alert_callback)
        monitor.start_monitoring()
        if not args.quiet:
            progress_manager.print_info("🔍 Performance monitoring enabled")

    # Create runner and run simulation
    game_config = config.create_game_config()
    runner = SimulationRunner(capital, args.output_dir, game_config)

    if not args.quiet:
        preset_info = f" ({args.preset} preset)" if args.preset else ""
        progress_manager.print_info(
            f"Running {sessions} sessions with {args.strategy} strategy{preset_info}"
        )
        progress_manager.print_info(f"Capital: {capital} LTC")
        if strategy_config.get("base_bet"):
            progress_manager.print_info(f"Base bet: {strategy_config['base_bet']} LTC")

    # Send start notification
    if slack_notifier:
        slack_notifier.notify_simulation_start(args.strategy, capital, sessions)

    try:
        results: dict[str, Any] = runner.run_strategy_simulation(
            strategy_config,
            sessions,
            session_config if session_config else None,
            parallel=args.parallel,
            show_progress=not args.no_progress,
            enable_detailed_logs=args.detailed_logs,
            log_dir=args.log_dir,
        )

        # Send completion notification
        if slack_notifier:
            slack_notifier.notify_simulation_complete(results["simulation_summary"])

    finally:
        # Stop monitoring
        if monitor:
            monitor.stop_monitoring()

    # Print summary
    if not args.quiet:
        print_simulation_summary(results)


def run_compare_command(args: Namespace) -> None:
    """Run strategy comparison command."""
    from dicebot.simulation.runner import SimulationRunner

    # Parse capital
    capital: Decimal = Decimal(args.capital)

    # Build strategy configs
    strategy_configs: list[dict[str, Any]] = []
    for strategy_name in args.strategies:
        config: dict[str, Any] = {
            "strategy": strategy_name,
            "base_bet": args.base_bet or "0.001",  # Default base bet
        }
        strategy_configs.append(config)

    # Create runner and run comparison
    runner = SimulationRunner(capital, args.output_dir)

    if not args.quiet:
        print(f"Comparing {len(args.strategies)} strategies with {args.sessions} sessions each...")
        print(f"Strategies: {', '.join(args.strategies)}")
        print(f"Capital: {capital} LTC")

    results: dict[str, Any] = runner.run_strategy_comparison(strategy_configs, args.sessions)

    # Print comparison summary
    if not args.quiet:
        print_comparison_summary(results)


def run_analyze_command(args: Namespace) -> None:
    """Run analysis command."""
    from dicebot.simulation.runner import SimulationRunner

    # Load results file
    runner = SimulationRunner(Decimal("0"))  # Dummy capital for analysis
    results: dict[str, Any] = runner.load_results_from_file(args.file)

    # Print analysis
    print_analysis(results, args.detailed)


def print_simulation_summary(results: dict[str, Any]) -> None:
    """Print simulation summary."""
    summary: dict[str, Any] = results["simulation_summary"]
    strategy_info: dict[str, Any] = results["strategy_info"]

    print("\n" + "=" * 60)
    print("SIMULATION SUMMARY")
    print("=" * 60)

    print(f"Strategy: {strategy_info['strategy_genome']['strategy_type']}")
    print(f"Sessions completed: {summary['total_sessions']}")
    print(f"Total bets: {summary['total_bets']:,}")
    print(f"Overall ROI: {summary['overall_roi']:.2%}")
    print(
        f"Profitable sessions: {summary['profitable_sessions']}/"
        f"{summary['total_sessions']} ({summary['profitability_rate']:.1%})"
    )
    print(f"Average win rate: {summary['average_win_rate']:.1%}")
    print(f"Worst drawdown: {summary['worst_drawdown']:.1%}")

    print("\nVault Status:")
    vault: dict[str, Any] = summary["vault_status"]
    print(f"  Final capital: {vault['total_capital']:.6f} LTC")
    print(f"  Net profit: {vault['net_profit']:.6f} LTC")

    if summary.get("stop_reasons"):
        print("\nStop reasons:")
        for reason, count in summary["stop_reasons"].items():
            print(f"  {reason}: {count} sessions")


def print_comparison_summary(results: dict[str, Any]) -> None:
    """Print comparison summary."""
    analysis: dict[str, Any] = results.get("comparison_analysis", {})

    print("\n" + "=" * 60)
    print("STRATEGY COMPARISON")
    print("=" * 60)

    if not analysis:
        print("No comparison data available")
        return

    rankings: dict[str, Any] = analysis.get("rankings", {})

    if "by_roi" in rankings:
        print("Rankings by ROI:")
        for i, (strategy, data) in enumerate(rankings["by_roi"][:5], 1):
            print(f"  {i}. {strategy}: {data['overall_roi']:.2%}")

    if "by_profitability_rate" in rankings:
        print("\nRankings by Profitability Rate:")
        for i, (strategy, data) in enumerate(rankings["by_profitability_rate"][:5], 1):
            rate: float = data["profitability_rate"]
            print(f"  {i}. {strategy}: {rate:.1%}")

    if "recommendations" in analysis:
        print("\nRecommendations:")
        for rec in analysis["recommendations"]:
            print(f"  • {rec}")

    stats: dict[str, Any] = analysis.get("statistics", {})
    if stats:
        print("\nOverall Statistics:")
        positive_roi: int = stats.get("strategies_with_positive_roi", 0)
        total_strats: int = stats.get("total_strategies", 0)
        print(f"  Strategies with positive ROI: {positive_roi}/{total_strats}")
        print(f"  Average ROI: {stats.get('average_roi', 0):.2%}")
        print(f"  Best ROI: {stats.get('best_roi', 0):.2%}")


def print_analysis(results: dict[str, Any], detailed: bool = False) -> None:
    """Print analysis of results file."""
    if "comparison_analysis" in results:
        print_comparison_summary(results)
    elif "simulation_summary" in results:
        print_simulation_summary(results)
    else:
        print("Unknown results format")
        return

    if detailed:
        print("\n" + "=" * 60)
        print("DETAILED DATA")
        print("=" * 60)
        print(json.dumps(results, indent=2, default=str))


def run_monitor_command(args: Namespace) -> None:
    """Run monitoring command."""
    import time

    from dicebot.integrations.monitoring import PerformanceMonitor
    from dicebot.integrations.slack_bot import SlackNotifier
    from dicebot.utils.progress import progress_manager

    progress_manager.print_info("🔍 Starting DiceBot Performance Monitor")

    # Setup Slack notifications if webhook provided
    slack_notifier: Any = None  # SlackNotifier type
    if args.slack_webhook:
        slack_notifier = SlackNotifier(args.slack_webhook)
        progress_manager.print_info("✅ Slack notifications enabled")

        # Test notification
        slack_notifier.notify_alert(
            "info",
            "DiceBot monitoring started",
        )

    # Setup alert callback
    def alert_callback(alert_type: str, message: str, severity: str) -> None:
        if slack_notifier:
            slack_notifier.notify_alert(alert_type, message)

        # Also log to console
        emoji_map: dict[str, str] = {"error": "🚨", "warning": "⚠️", "success": "✅", "info": "ℹ️"}
        emoji: str = emoji_map.get(alert_type, "🔔")
        progress_manager.print(f"{emoji} [{severity.upper()}] {message}")  # type: ignore[no-untyped-call]

    # Create monitor
    monitor = PerformanceMonitor(alert_callback=alert_callback, check_interval=args.check_interval)

    # Set custom thresholds if provided
    if args.cpu_warning:
        monitor.set_threshold("cpu_warning", args.cpu_warning)
    if args.memory_warning:
        monitor.set_threshold("memory_warning", args.memory_warning)

    # Start monitoring
    monitor.start_monitoring()

    try:
        progress_manager.print_info(
            f"🎯 Monitoring active (check interval: {args.check_interval}s)"
        )
        progress_manager.print_info("Press Ctrl+C to stop monitoring")

        while True:
            time.sleep(5)

            # Show periodic status
            summary: dict[str, Any] = monitor.get_performance_summary()
            if summary and not summary.get("error"):
                system: dict[str, Any] = summary["system"]
                sessions: dict[str, Any] = summary["sessions"]

                progress_manager.print(  # type: ignore[no-untyped-call]
                    f"📊 CPU: {system['cpu_percent']:.1f}% | "
                    f"Memory: {system['memory_percent']:.1f}% | "
                    f"Active sessions: {sessions['active_count']}"
                )

    except KeyboardInterrupt:
        progress_manager.print_info("\n🛑 Stopping monitor...")
        monitor.stop_monitoring()

        if slack_notifier:
            slack_notifier.notify_alert("info", "DiceBot monitoring stopped")

        progress_manager.print_info("✅ Monitor stopped")


def run_recovery_command(args: Namespace) -> None:
    """Run recovery command."""
    from dicebot.utils.checkpoint import checkpoint_manager
    from dicebot.utils.progress import progress_manager

    if args.recovery_command == "list":
        checkpoints: list[dict[str, Any]] = checkpoint_manager.list_checkpoints()

        if not checkpoints:
            progress_manager.print_info("No checkpoints found")
            return

        progress_manager.print_info(f"Found {len(checkpoints)} checkpoints:")

        for cp in checkpoints:
            strategy: str = cp["strategy_config"].get("strategy", "unknown")
            remaining: int = cp.get("remaining_sessions", 0)
            age_hours: float = cp["file_age_hours"]

            status: str = "✅ Completed" if remaining == 0 else f"⏸️  {remaining} sessions remaining"
            age_str: str = (
                f"{age_hours:.1f}h ago" if age_hours < 24 else f"{age_hours / 24:.1f}d ago"
            )

            progress_manager.print(  # type: ignore[no-untyped-call]
                f"  📁 {cp['simulation_id']}: {strategy} strategy | {status} | {age_str}"
            )

    elif args.recovery_command == "resume":
        progress_manager.print_info(f"Resuming simulation: {args.simulation_id}")

        checkpoint_data: dict[str, Any] | None = checkpoint_manager.load_checkpoint(
            args.simulation_id
        )
        if not checkpoint_data:
            progress_manager.print_error(f"Checkpoint not found: {args.simulation_id}")
            return

        # Resume the simulation (simplified implementation)
        progress_manager.print_info("Checkpoint recovery feature coming soon!")
        progress_manager.print_info(
            f"Found checkpoint with "
            f"{len(checkpoint_data.get('completed_sessions', []))} "
            f"completed sessions"
        )

    elif args.recovery_command == "clean":
        progress_manager.print_info(f"Cleaning checkpoints older than {args.max_age} days...")
        # TODO: Need to add public API for checkpoint cleanup
        # For now, this functionality is not available
        progress_manager.print_warning("Checkpoint cleanup not yet implemented")

    else:
        progress_manager.print_error("Invalid recovery command")


if __name__ == "__main__":
    main()
