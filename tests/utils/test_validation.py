"""Tests pour le système de validation."""

from decimal import Decimal

import pytest

from dicebot.utils.validation import ParameterValidator, RiskLevel, ValidationError


class TestParameterValidator:
    """Test le validateur de paramètres."""

    def test_validate_strategy_config_safe(self) -> None:
        """Test validation d'une configuration sûre."""
        config = {"strategy": "fibonacci", "base_bet": "0.001", "max_losses": 8}
        capital = Decimal("100")

        warnings = ParameterValidator.validate_strategy_config(config, capital)

        # Configuration sûre ne devrait pas générer d'avertissements
        assert len(warnings) == 0

    def test_validate_strategy_config_high_base_bet(self) -> None:
        """Test validation avec mise de base élevée."""
        config = {
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
        config = {
            "strategy": "martingale",
            "base_bet": "25.0",  # 25% du capital
            "max_losses": 5,
        }
        capital = Decimal("100")

        warnings = ParameterValidator.validate_strategy_config(config, capital)

        # Devrait générer un avertissement critique
        assert len(warnings) > 0
        assert any("very risky" in warning.lower() for warning in warnings.values())

    def test_validate_strategy_config_high_max_losses(self) -> None:
        """Test validation avec max_losses élevé."""
        config = {
            "strategy": "martingale",
            "base_bet": "0.001",
            "max_losses": 20,  # Très élevé pour Martingale
        }
        capital = Decimal("100")

        warnings = ParameterValidator.validate_strategy_config(config, capital)

        # Devrait générer un avertissement sur max_losses
        assert len(warnings) > 0

    def test_calculate_martingale_max_safe_losses(self) -> None:
        """Test le calcul des pertes max sûres pour Martingale."""
        capital = Decimal("100")
        base_bet = Decimal("0.001")

        max_safe = ParameterValidator.calculate_martingale_max_safe_losses(capital, base_bet)

        # Devrait être un nombre raisonnable
        assert 1 <= max_safe <= 20

        # Vérifier que c'est effectivement sûr
        total_risk = base_bet * (2**max_safe - 1)
        assert total_risk <= capital * Decimal("0.5")  # Max 50% du capital

    def test_calculate_martingale_max_safe_losses_high_base_bet(self) -> None:
        """Test avec une mise de base élevée."""
        capital = Decimal("100")
        base_bet = Decimal("10")  # 10% du capital

        max_safe = ParameterValidator.calculate_martingale_max_safe_losses(capital, base_bet)

        # Avec une mise élevée, max_safe devrait être très bas
        assert max_safe <= 5

    def test_estimate_fibonacci_requirement(self) -> None:
        """Test l'estimation des besoins Fibonacci."""
        base_bet = Decimal("0.001")
        max_losses = 10

        requirement = ParameterValidator.estimate_fibonacci_requirement(base_bet, max_losses)

        # Devrait être plus élevé que base_bet mais raisonnable
        assert requirement > base_bet
        assert requirement < base_bet * 100  # Pas trop élevé

    def test_suggest_safer_base_bet(self) -> None:
        """Test les suggestions de mise plus sûre."""
        capital = Decimal("100")

        # Test différents pourcentages
        suggestion_1pct = ParameterValidator.suggest_safer_base_bet(capital, 0.01)
        suggestion_2pct = ParameterValidator.suggest_safer_base_bet(capital, 0.02)

        assert suggestion_1pct == Decimal("1.0")  # 1% de 100
        assert suggestion_2pct == Decimal("2.0")  # 2% de 100

        # Vérifier le minimum
        small_capital = Decimal("1")
        suggestion_min = ParameterValidator.suggest_safer_base_bet(small_capital, 0.01)
        assert suggestion_min >= Decimal("0.00015")  # Minimum Bitsler

    def test_assess_risk_level_low(self) -> None:
        """Test évaluation risque faible."""
        config = {"strategy": "flat", "base_bet": "0.001", "max_losses": 5}
        capital = Decimal("100")

        risk = ParameterValidator.assess_risk_level(config, capital)

        assert risk == RiskLevel.LOW

    def test_assess_risk_level_medium(self) -> None:
        """Test évaluation risque moyen."""
        config = {
            "strategy": "fibonacci",
            "base_bet": "0.005",  # 0.5% du capital
            "max_losses": 10,
        }
        capital = Decimal("100")

        risk = ParameterValidator.assess_risk_level(config, capital)

        assert risk in [RiskLevel.LOW, RiskLevel.MEDIUM]

    def test_assess_risk_level_high(self) -> None:
        """Test évaluation risque élevé."""
        config = {
            "strategy": "martingale",
            "base_bet": "2.0",  # 2% du capital
            "max_losses": 15,
        }
        capital = Decimal("100")

        risk = ParameterValidator.assess_risk_level(config, capital)

        assert risk in [RiskLevel.HIGH, RiskLevel.EXTREME]

    def test_assess_risk_level_extreme(self) -> None:
        """Test évaluation risque extrême."""
        config = {
            "strategy": "martingale",
            "base_bet": "10.0",  # 10% du capital
            "max_losses": 20,
        }
        capital = Decimal("100")

        risk = ParameterValidator.assess_risk_level(config, capital)

        assert risk == RiskLevel.EXTREME

    def test_validate_with_suggestions(self) -> None:
        """Test que la validation inclut des suggestions."""
        config = {"strategy": "martingale", "base_bet": "5.0", "max_losses": 15}
        capital = Decimal("100")

        warnings = ParameterValidator.validate_strategy_config(config, capital)

        # Devrait inclure des suggestions d'amélioration
        suggestion_found = False
        for warning in warnings.values():
            if "consider" in warning.lower() or "reduce" in warning.lower():
                suggestion_found = True
                break

        assert suggestion_found

    def test_edge_case_zero_capital(self) -> None:
        """Test cas limite avec capital zéro."""
        config = {"strategy": "flat", "base_bet": "0.001"}
        capital = Decimal("0")

        warnings = ParameterValidator.validate_strategy_config(config, capital)

        # Devrait générer un avertissement critique
        assert len(warnings) > 0

    def test_edge_case_negative_values(self) -> None:
        """Test cas limite avec valeurs négatives."""
        config = {"strategy": "flat", "base_bet": "-0.001", "max_losses": -5}
        capital = Decimal("100")

        warnings = ParameterValidator.validate_strategy_config(config, capital)

        # Devrait gérer les valeurs négatives
        assert len(warnings) > 0

    def test_string_to_decimal_conversion(self) -> None:
        """Test conversion string vers Decimal."""
        config = {
            "strategy": "flat",
            "base_bet": "0.001000",  # Avec zéros supplémentaires
            "max_losses": "5",
        }
        capital = Decimal("100")

        # Ne devrait pas lever d'exception
        warnings = ParameterValidator.validate_strategy_config(config, capital)

        # Devrait traiter correctement les strings
        assert isinstance(warnings, dict)

    def test_different_strategies_different_validation(self) -> None:
        """Test que différentes stratégies ont des validations différentes."""
        base_config = {"base_bet": "1.0", "max_losses": 10}
        capital = Decimal("100")

        # Martingale devrait être plus risqué que Flat
        martingale_config = {**base_config, "strategy": "martingale"}
        flat_config = {**base_config, "strategy": "flat"}

        martingale_warnings = ParameterValidator.validate_strategy_config(
            martingale_config, capital
        )
        flat_warnings = ParameterValidator.validate_strategy_config(flat_config, capital)

        # Martingale devrait générer plus ou des avertissements plus sévères
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
