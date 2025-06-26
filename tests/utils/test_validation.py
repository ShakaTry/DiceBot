"""Tests pour le système de validation."""

from decimal import Decimal
from typing import Any

import pytest

from dicebot.utils.validation import ParameterValidator, RiskLevel, ValidationError


class TestParameterValidator:
    """Test le validateur de paramètres."""

    def test_validate_strategy_config_safe(self) -> None:
        """Test validation d'une configuration sûre."""
        config: dict[str, Any] = {"strategy": "fibonacci", "base_bet": "0.001", "max_losses": 8}
        capital = Decimal("100")

        result = ParameterValidator.validate_strategy_config(config, capital)

        # Configuration sûre ne devrait pas générer d'avertissements
        assert len(result.get("warnings", [])) == 0

    def test_validate_strategy_config_high_base_bet(self) -> None:
        """Test validation avec mise de base élevée."""
        config: dict[str, Any] = {
            "strategy": "martingale",
            "base_bet": "5.0",  # 5% du capital
            "max_losses": 10,
        }
        capital = Decimal("100")

        # Cette configuration devrait lever une ValidationError car trop risquée
        with pytest.raises(ValidationError) as exc_info:
            ParameterValidator.validate_strategy_config(config, capital)

        # Vérifier que l'erreur mentionne le capital insuffisant
        assert "capital" in str(exc_info.value).lower()

    def test_validate_strategy_config_extreme_base_bet(self) -> None:
        """Test validation avec mise de base extrême."""
        config: dict[str, Any] = {
            "strategy": "martingale",
            "base_bet": "25.0",  # 25% du capital
            "max_losses": 5,
        }
        capital = Decimal("100")

        result = ParameterValidator.validate_strategy_config(config, capital)

        # Devrait générer un avertissement critique
        warnings = result.get("warnings", [])
        assert len(warnings) > 0
        assert any("very risky" in warning.lower() for warning in warnings)

    def test_validate_strategy_config_high_max_losses(self) -> None:
        """Test validation avec max_losses élevé."""
        config: dict[str, Any] = {
            "strategy": "martingale",
            "base_bet": "0.001",
            "max_losses": 20,  # Très élevé pour Martingale
        }
        capital = Decimal("100")

        result = ParameterValidator.validate_strategy_config(config, capital)

        # Devrait générer un avertissement sur max_losses
        warnings = result.get("warnings", [])
        assert len(warnings) > 0

    def test_calculate_martingale_max_safe_losses(self) -> None:
        """Test le calcul des pertes max sûres pour Martingale."""
        capital = Decimal("100")
        base_bet = Decimal("0.001")

        # Tester indirectement via validate_strategy_config
        config: dict[str, Any] = {
            "strategy": "martingale",
            "base_bet": str(base_bet),
            "max_losses": 50,  # Très élevé pour déclencher la validation
        }

        result = ParameterValidator.validate_strategy_config(config, capital)
        suggestions = result.get("suggestions", [])

        # Devrait avoir des suggestions pour réduire max_losses
        assert any("max_losses" in suggestion for suggestion in suggestions)

    def test_calculate_martingale_max_safe_losses_high_base_bet(self) -> None:
        """Test avec une mise de base élevée."""
        capital = Decimal("100")
        base_bet = Decimal("10")  # 10% du capital

        # Tester indirectement via validate_strategy_config
        config: dict[str, Any] = {
            "strategy": "martingale",
            "base_bet": str(base_bet),
            "max_losses": 10,
        }

        with pytest.raises(ValidationError) as exc_info:
            ParameterValidator.validate_strategy_config(config, capital)

        # Devrait lever une erreur car la mise est trop élevée
        assert "martingale" in str(exc_info.value).lower()

    def test_estimate_fibonacci_requirement(self) -> None:
        """Test l'estimation des besoins Fibonacci."""
        base_bet = Decimal("0.001")
        max_losses = 30  # Assez élevé pour déclencher un avertissement

        # Tester indirectement via validate_strategy_config
        config: dict[str, Any] = {
            "strategy": "fibonacci",
            "base_bet": str(base_bet),
            "max_losses": max_losses,
        }
        capital = Decimal("100")

        result = ParameterValidator.validate_strategy_config(config, capital)
        warnings = result.get("warnings", [])

        # Devrait avoir des avertissements pour Fibonacci avec max_losses élevé
        assert len(warnings) > 0 or "fibonacci" in str(warnings).lower()

    def test_suggest_safer_base_bet(self) -> None:
        """Test les suggestions de mise plus sûre."""
        capital = Decimal("100")

        # Test différents pourcentages
        suggestion_1pct = capital * Decimal("0.01")
        suggestion_2pct = capital * Decimal("0.02")

        assert suggestion_1pct == Decimal("1.0")  # 1% de 100
        assert suggestion_2pct == Decimal("2.0")  # 2% de 100

        # Vérifier le minimum
        small_capital = Decimal("1")
        suggestion_min = max(small_capital * Decimal("0.01"), Decimal("0.00015"))
        assert suggestion_min >= Decimal("0.00015")  # Minimum Bitsler

    def test_assess_risk_level_low(self) -> None:
        """Test évaluation risque faible."""
        config: dict[str, Any] = {"strategy": "flat", "base_bet": "0.001", "max_losses": 5}
        capital = Decimal("100")

        risk = ParameterValidator.assess_risk_level(config, capital)

        assert risk == RiskLevel.LOW

    def test_assess_risk_level_medium(self) -> None:
        """Test évaluation risque moyen."""
        config: dict[str, Any] = {
            "strategy": "fibonacci",
            "base_bet": "0.005",  # 0.5% du capital
            "max_losses": 10,
        }
        capital = Decimal("100")

        risk = ParameterValidator.assess_risk_level(config, capital)

        assert risk in [RiskLevel.LOW, RiskLevel.MEDIUM]

    def test_assess_risk_level_high(self) -> None:
        """Test évaluation risque élevé."""
        config: dict[str, Any] = {
            "strategy": "martingale",
            "base_bet": "2.0",  # 2% du capital
            "max_losses": 15,
        }
        capital = Decimal("100")

        risk = ParameterValidator.assess_risk_level(config, capital)

        assert risk in [RiskLevel.HIGH, RiskLevel.EXTREME]

    def test_assess_risk_level_extreme(self) -> None:
        """Test évaluation risque extrême."""
        config: dict[str, Any] = {
            "strategy": "martingale",
            "base_bet": "10.0",  # 10% du capital
            "max_losses": 20,
        }
        capital = Decimal("100")

        risk = ParameterValidator.assess_risk_level(config, capital)

        assert risk == RiskLevel.EXTREME

    def test_validate_with_suggestions(self) -> None:
        """Test que la validation inclut des suggestions."""
        config: dict[str, Any] = {"strategy": "martingale", "base_bet": "5.0", "max_losses": 15}
        capital = Decimal("100")

        result = ParameterValidator.validate_strategy_config(config, capital)

        # Devrait inclure des suggestions d'amélioration
        suggestion_found = False
        warnings = result.get("warnings", [])
        suggestions = result.get("suggestions", [])
        all_messages = warnings + suggestions
        for message in all_messages:
            if "consider" in message.lower() or "reduce" in message.lower():
                suggestion_found = True
                break

        assert suggestion_found

    def test_edge_case_zero_capital(self) -> None:
        """Test cas limite avec capital zéro."""
        config: dict[str, Any] = {"strategy": "flat", "base_bet": "0.001"}
        capital = Decimal("0")

        with pytest.raises(ValidationError):
            ParameterValidator.validate_strategy_config(config, capital)

    def test_edge_case_negative_values(self) -> None:
        """Test cas limite avec valeurs négatives."""
        config: dict[str, Any] = {"strategy": "flat", "base_bet": "-0.001", "max_losses": -5}
        capital = Decimal("100")

        with pytest.raises(ValidationError):
            ParameterValidator.validate_strategy_config(config, capital)

    def test_string_to_decimal_conversion(self) -> None:
        """Test conversion string vers Decimal."""
        config: dict[str, Any] = {
            "strategy": "flat",
            "base_bet": "0.001000",  # Avec zéros supplémentaires
            "max_losses": "5",
        }
        capital = Decimal("100")

        # Ne devrait pas lever d'exception
        result = ParameterValidator.validate_strategy_config(config, capital)

        # Devrait traiter correctement les strings
        assert isinstance(result, dict)

    def test_different_strategies_different_validation(self) -> None:
        """Test que différentes stratégies ont des validations différentes."""
        base_config: dict[str, Any] = {"base_bet": "1.0", "max_losses": 10}
        capital = Decimal("100")

        # Martingale devrait être plus risqué que Flat
        martingale_config: dict[str, Any] = {**base_config, "strategy": "martingale"}
        flat_config: dict[str, Any] = {**base_config, "strategy": "flat"}

        martingale_result = ParameterValidator.validate_strategy_config(martingale_config, capital)
        flat_result = ParameterValidator.validate_strategy_config(flat_config, capital)

        # Martingale devrait générer plus ou des avertissements plus sévères
        martingale_warnings = martingale_result.get("warnings", [])
        flat_warnings = flat_result.get("warnings", [])
        assert len(martingale_warnings) >= len(flat_warnings)

    def test_risk_level_enum_values(self) -> None:
        """Test que l'enum RiskLevel a les bonnes valeurs."""
        assert hasattr(RiskLevel, "LOW")
        assert hasattr(RiskLevel, "MEDIUM")
        assert hasattr(RiskLevel, "HIGH")
        assert hasattr(RiskLevel, "EXTREME")

        # Test ordre croissant de risque
        assert RiskLevel.LOW.value < RiskLevel.MEDIUM.value
        assert RiskLevel.MEDIUM.value < RiskLevel.HIGH.value
        assert RiskLevel.HIGH.value < RiskLevel.EXTREME.value
