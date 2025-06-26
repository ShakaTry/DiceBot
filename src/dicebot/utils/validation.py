"""
Parameter validation utilities for DiceBot.
"""

import math
from decimal import Decimal
from enum import Enum, auto
from typing import Any

from ..core.constants import MAX_BET_LTC, MIN_BET_LTC
from .progress import progress_manager


class ValidationError(Exception):
    """Custom exception for validation errors."""

    pass


class RiskLevel(Enum):
    """Niveaux de risque pour les configurations."""

    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    EXTREME = auto()


class ParameterValidator:
    """Validator for DiceBot parameters and configurations."""

    @staticmethod
    def validate_capital(capital: str | Decimal) -> Decimal:
        """Validate and convert capital amount.

        Args:
            capital: Capital amount as string or Decimal

        Returns:
            Validated Decimal capital amount

        Raises:
            ValidationError: If capital is invalid
        """
        try:
            capital_decimal = Decimal(str(capital))
        except (ValueError, TypeError) as e:
            raise ValidationError(f"Invalid capital format: {capital}") from e

        if capital_decimal <= 0:
            raise ValidationError("Capital must be positive")

        if capital_decimal < MIN_BET_LTC:
            raise ValidationError(f"Capital must be at least {MIN_BET_LTC} LTC")

        # Warn for very small capitals
        if capital_decimal < Decimal("1.0"):
            progress_manager.print_warning(
                f"Capital is very small ({capital_decimal} LTC). "
                "Consider using at least 1 LTC for meaningful simulations."
            )

        return capital_decimal

    @staticmethod
    def validate_strategy_config(
        strategy_config: dict[str, Any], capital: Decimal
    ) -> dict[str, Any]:
        """Validate strategy configuration and return suggestions.

        Args:
            strategy_config: Strategy configuration dictionary
            capital: Total capital

        Returns:
            Dictionary of validation results and suggestions

        Raises:
            ValidationError: If configuration is invalid
        """
        errors: list[str] = []
        warnings: list[str] = []
        suggestions: list[str] = []

        strategy_name = strategy_config.get("strategy")
        if not strategy_name:
            errors.append("Strategy name is required")

        # Validate base_bet
        base_bet_str = strategy_config.get("base_bet", "0.001")
        try:
            base_bet = Decimal(str(base_bet_str))
        except (ValueError, TypeError):
            errors.append(f"Invalid base_bet format: {base_bet_str}")
            return {"errors": errors, "warnings": warnings, "suggestions": suggestions}

        if base_bet <= 0:
            errors.append("base_bet must be positive")

        if base_bet < MIN_BET_LTC:
            errors.append(f"base_bet must be at least {MIN_BET_LTC} LTC")

        if base_bet > MAX_BET_LTC:
            errors.append(f"base_bet must not exceed {MAX_BET_LTC} LTC")

        if base_bet > capital:
            errors.append(f"base_bet ({base_bet}) cannot exceed capital ({capital})")

        # Capital ratio validation
        capital_ratio = float(base_bet / capital)
        if capital_ratio > 0.1:  # More than 10% of capital
            warnings.append(f"base_bet is {capital_ratio:.1%} of capital - very risky")
            safer_bet = capital * Decimal("0.01")  # 1% of capital
            suggestions.append(f"Consider reducing base_bet to {safer_bet:.6f} LTC (1% of capital)")

        # Validate max_losses
        max_losses = strategy_config.get("max_losses", 10)
        if not isinstance(max_losses, int) or max_losses < 1:
            errors.append("max_losses must be a positive integer")

        if max_losses > 50:
            warnings.append(f"max_losses ({max_losses}) is very high - extreme risk")

        # Strategy-specific validation
        if strategy_name == "martingale":
            max_possible_bet = ParameterValidator._calculate_martingale_max_bet(
                base_bet, max_losses, strategy_config.get("multiplier", 2.0)
            )
            if max_possible_bet > capital:
                errors.append(
                    f"Martingale strategy would require {max_possible_bet:.6f} LTC "
                    f"but capital is only {capital:.6f} LTC"
                )
                suggested_max_losses = ParameterValidator._suggest_martingale_max_losses(
                    base_bet, capital, strategy_config.get("multiplier", 2.0)
                )
                suggestions.append(f"Reduce max_losses to {suggested_max_losses} or less")

        elif strategy_name == "fibonacci":
            max_fib_bet = ParameterValidator._calculate_fibonacci_max_bet(base_bet, max_losses)
            if max_fib_bet > capital * Decimal("0.5"):  # More than 50% of capital
                warnings.append(
                    f"Fibonacci sequence could reach {max_fib_bet:.6f} LTC "
                    f"({float(max_fib_bet / capital):.1%} of capital)"
                )

        # Risk level assessment
        risk_level = ParameterValidator.assess_risk_level(strategy_config, capital)

        if risk_level == RiskLevel.EXTREME:
            warnings.append("Risk level: EXTREME - not recommended")
            # suggestions.extend(config.suggest_improvements(strategy_config, capital))
        elif risk_level == RiskLevel.HIGH:
            warnings.append("Risk level: HIGH - use with caution")

        if errors:
            raise ValidationError(f"Validation failed: {'; '.join(errors)}")

        return {
            "errors": errors,
            "warnings": warnings,
            "suggestions": suggestions,
            "risk_level": risk_level,
        }

    @staticmethod
    def validate_session_config(session_config: dict[str, Any]) -> dict[str, Any]:
        """Validate session configuration.

        Args:
            session_config: Session configuration dictionary

        Returns:
            Dictionary of validation results
        """
        warnings: list[str] = []
        suggestions: list[str] = []

        # Validate stop_loss
        if "stop_loss" in session_config:
            stop_loss = session_config["stop_loss"]
            if isinstance(stop_loss, int | float):
                if stop_loss >= 0:
                    warnings.append("stop_loss should be negative (e.g., -0.1 for -10%)")
                if stop_loss < -0.5:
                    warnings.append("stop_loss is very strict (< -50%)")

        # Validate take_profit
        if "take_profit" in session_config:
            take_profit = session_config["take_profit"]
            if isinstance(take_profit, int | float):
                if take_profit <= 0:
                    warnings.append("take_profit should be positive (e.g., 0.2 for 20%)")
                if take_profit > 2.0:
                    warnings.append("take_profit is very optimistic (> 200%)")

        # Validate max_bets
        if "max_bets" in session_config:
            max_bets = session_config["max_bets"]
            if not isinstance(max_bets, int) or max_bets < 1:
                warnings.append("max_bets must be a positive integer")
            elif max_bets > 10000:
                warnings.append("max_bets is very high - sessions may take a long time")

        return {"warnings": warnings, "suggestions": suggestions}

    @staticmethod
    def estimate_session_duration(
        strategy_config: dict[str, Any], session_config: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Estimate session duration and resource usage.

        Args:
            strategy_config: Strategy configuration
            session_config: Session configuration

        Returns:
            Dictionary with estimates
        """
        session_config = session_config or {}

        # Base estimates (very rough)
        Decimal(str(strategy_config.get("base_bet", "0.001")))
        max_losses = strategy_config.get("max_losses", 10)

        # Estimate based on strategy type and aggressiveness
        strategy_name = strategy_config.get("strategy", "flat")

        if strategy_name == "martingale":
            # Aggressive strategies tend to end sessions faster (win big or lose all)
            estimated_bets = max_losses * 2 + 50  # Very rough estimate
        elif strategy_name == "fibonacci":
            estimated_bets = max_losses * 3 + 100
        else:
            estimated_bets = 200  # Default estimate

        # Factor in session limits
        max_bets = session_config.get("max_bets")
        if max_bets and max_bets < estimated_bets:
            estimated_bets = max_bets

        # Very rough time estimates (assuming ~0.01s per bet in simulation)
        estimated_time_seconds = estimated_bets * 0.01

        return {
            "estimated_bets": estimated_bets,
            "estimated_time_seconds": estimated_time_seconds,
            "estimated_time_formatted": f"{estimated_time_seconds:.1f}s",
            "memory_usage_mb": estimated_bets * 0.001,  # Very rough
        }

    @staticmethod
    def _calculate_martingale_max_bet(
        base_bet: Decimal, max_losses: int, multiplier: float
    ) -> Decimal:
        """Calculate maximum bet for Martingale strategy."""
        return base_bet * (Decimal(str(multiplier)) ** max_losses)

    @staticmethod
    def _suggest_martingale_max_losses(
        base_bet: Decimal, capital: Decimal, multiplier: float
    ) -> int:
        """Suggest safe max_losses for Martingale strategy."""
        if base_bet >= capital:
            return 1

        ratio = float(capital / base_bet)
        return max(1, int(math.log(ratio, multiplier)) - 1)

    @staticmethod
    def _calculate_fibonacci_max_bet(base_bet: Decimal, max_losses: int) -> Decimal:
        """Calculate maximum bet for Fibonacci strategy."""
        # Generate fibonacci sequence up to max_losses
        if max_losses <= 0:
            return base_bet

        fib = [1, 1]
        for i in range(2, max_losses):
            fib.append(fib[i - 1] + fib[i - 2])

        max_multiplier = fib[min(len(fib) - 1, max_losses - 1)]
        return base_bet * Decimal(str(max_multiplier))

    @staticmethod
    def assess_risk_level(config: dict[str, Any], capital: Decimal) -> RiskLevel:
        """
        Évalue le niveau de risque d'une configuration.

        Args:
            config: Configuration de la stratégie
            capital: Capital total

        Returns:
            Niveau de risque
        """
        try:
            strategy_name = config.get("strategy", "flat")
            base_bet = Decimal(str(config.get("base_bet", "0.001")))
            max_losses = int(config.get("max_losses", 10))

            if capital <= 0:
                return RiskLevel.EXTREME

            capital_ratio = float(base_bet / capital)

            # Risque basé sur le ratio capital
            if capital_ratio > 0.1:  # Plus de 10%
                return RiskLevel.EXTREME
            elif capital_ratio > 0.05:  # Plus de 5%
                return RiskLevel.HIGH
            elif capital_ratio > 0.02:  # Plus de 2%
                return RiskLevel.MEDIUM

            # Risque basé sur la stratégie
            if strategy_name == "martingale":
                if max_losses > 15:
                    return RiskLevel.EXTREME
                elif max_losses > 10:
                    return RiskLevel.HIGH
                elif max_losses > 5:
                    return RiskLevel.MEDIUM

            elif strategy_name in ["fibonacci", "dalembert"]:
                if max_losses > 20:
                    return RiskLevel.HIGH
                elif max_losses > 15:
                    return RiskLevel.MEDIUM

            return RiskLevel.LOW

        except (ValueError, TypeError):
            return RiskLevel.EXTREME


def validate_and_suggest(
    strategy_config: dict[str, Any],
    capital: Decimal,
    session_config: dict[str, Any] | None = None,
    show_output: bool = True,
) -> bool:
    """Validate configuration and show suggestions.

    Args:
        strategy_config: Strategy configuration
        capital: Total capital
        session_config: Session configuration
        show_output: Whether to print validation results

    Returns:
        True if validation passed, False otherwise
    """
    try:
        # Validate strategy config
        strategy_results = ParameterValidator.validate_strategy_config(strategy_config, capital)

        # Validate session config
        session_results = {"warnings": [], "suggestions": []}
        if session_config:
            session_results = ParameterValidator.validate_session_config(session_config)

        # Show results
        if show_output:
            # Show warnings
            all_warnings = strategy_results["warnings"] + session_results["warnings"]
            for warning in all_warnings:
                progress_manager.print_warning(warning)

            # Show suggestions
            all_suggestions = strategy_results["suggestions"] + session_results["suggestions"]
            for suggestion in all_suggestions:
                progress_manager.print_info(f"💡 {suggestion}")

            # Show risk level
            if "risk_level" in strategy_results:
                risk_level = strategy_results["risk_level"]
                if risk_level in [RiskLevel.HIGH, RiskLevel.EXTREME]:
                    progress_manager.print_warning(f"Risk level: {risk_level.name}")
                else:
                    progress_manager.print_info(f"Risk level: {risk_level.name}")

        return True

    except ValidationError as e:
        if show_output:
            progress_manager.print_error(str(e))
        return False
