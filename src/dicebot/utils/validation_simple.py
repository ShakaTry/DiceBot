"""
Simplified parameter validation utilities for DiceBot.
"""

import math
from decimal import Decimal
from enum import Enum, auto
from typing import Any

from ..core.constants import MIN_BET_LTC


class RiskLevel(Enum):
    """Niveaux de risque pour les configurations."""

    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    EXTREME = auto()


class ParameterValidator:
    """Validator for DiceBot parameters and configurations."""

    @staticmethod
    def validate_strategy_config(config: dict[str, Any], capital: Decimal) -> dict[str, str]:
        """
        Valide une configuration de stratégie.

        Args:
            config: Configuration de la stratégie
            capital: Capital total disponible

        Returns:
            Dict avec les avertissements trouvés
        """
        warnings = {}

        try:
            strategy_name = config.get("strategy", "unknown")
            base_bet = Decimal(str(config.get("base_bet", "0.001")))
            max_losses = int(config.get("max_losses", 10))

            # Validation base_bet
            if base_bet <= 0:
                warnings["base_bet"] = "base_bet must be positive"
                return warnings

            capital_ratio = float(base_bet / capital) if capital > 0 else 1.0

            if capital_ratio > 0.1:  # Plus de 10% du capital
                safer_bet = capital * Decimal("0.01")  # 1% du capital
                warnings["base_bet"] = (
                    f"base_bet is {capital_ratio:.1%} of capital - very risky. Consider reducing base_bet to {safer_bet:.6f} LTC (1% of capital)"
                )
            elif capital_ratio > 0.05:  # Plus de 5% du capital
                warnings["base_bet"] = f"base_bet is {capital_ratio:.1%} of capital - risky"

            # Validation max_losses
            if max_losses > 20:
                warnings["max_losses"] = f"max_losses ({max_losses}) is very high - extreme risk"
            elif max_losses > 15:
                warnings["max_losses"] = f"max_losses ({max_losses}) is high - use with caution"

            # Validation spécifique Martingale
            if strategy_name == "martingale" and max_losses > 0:
                max_possible_bet = base_bet * (2**max_losses)
                if max_possible_bet > capital:
                    safe_losses = int(math.log2(float(capital / base_bet)))
                    warnings["martingale"] = (
                        f"Martingale would require {max_possible_bet:.6f} LTC but capital is only {capital:.6f} LTC. Consider max_losses <= {safe_losses}"
                    )

            # Assessment du risque global
            risk_level = ParameterValidator.assess_risk_level(config, capital)
            if risk_level == RiskLevel.EXTREME:
                warnings["risk"] = "Risk level: EXTREME - not recommended"
            elif risk_level == RiskLevel.HIGH:
                warnings["risk"] = "Risk level: HIGH - use with caution"

        except (ValueError, TypeError, ZeroDivisionError) as e:
            warnings["validation_error"] = f"Validation error: {e}"

        return warnings

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

    @staticmethod
    def calculate_martingale_max_safe_losses(capital: Decimal, base_bet: Decimal) -> int:
        """
        Calcule le nombre maximum de pertes consécutives sûres pour Martingale.

        Args:
            capital: Capital total
            base_bet: Mise de base

        Returns:
            Nombre maximum de pertes consécutives sûres
        """
        if base_bet <= 0 or capital <= 0:
            return 0

        # Calculer pour que le total des mises ne dépasse pas 50% du capital
        max_total = capital * Decimal("0.5")

        max_losses = 0
        total_risk = Decimal("0")

        while total_risk + base_bet * (2**max_losses) <= max_total:
            total_risk += base_bet * (2**max_losses)
            max_losses += 1

            # Limiter à un maximum raisonnable
            if max_losses >= 20:
                break

        return max(1, max_losses - 1)

    @staticmethod
    def estimate_fibonacci_requirement(base_bet: Decimal, max_losses: int) -> Decimal:
        """
        Estime le capital requis pour une stratégie Fibonacci.

        Args:
            base_bet: Mise de base
            max_losses: Nombre maximum de pertes

        Returns:
            Capital estimé requis
        """
        if max_losses <= 0:
            return base_bet

        # Séquence de Fibonacci limitée à max_losses
        fib_sequence = [1, 1]
        for i in range(2, max_losses + 1):
            fib_sequence.append(fib_sequence[i - 1] + fib_sequence[i - 2])

        # Somme de toutes les mises possibles
        total_requirement = sum(fib_sequence[:max_losses]) * base_bet

        return total_requirement

    @staticmethod
    def suggest_safer_base_bet(capital: Decimal, percentage: float = 0.01) -> Decimal:
        """
        Suggère une mise de base plus sûre.

        Args:
            capital: Capital total
            percentage: Pourcentage du capital (défaut: 1%)

        Returns:
            Mise de base suggérée
        """
        if capital <= 0:
            return MIN_BET_LTC

        suggested = capital * Decimal(str(percentage))

        # Respecter les limites minimales
        return max(suggested, MIN_BET_LTC)
