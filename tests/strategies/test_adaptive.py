"""Tests pour AdaptiveStrategy."""

from decimal import Decimal

from dicebot.core.models import BetResult, GameState
from dicebot.strategies import (
    AdaptiveConfig,
    AdaptiveStrategy,
    StrategyRule,
    SwitchCondition,
)


class TestAdaptiveStrategy:
    """Test la stratégie adaptative."""

    def setup_method(self) -> None:
        """Prépare les tests."""
        self.game_state = GameState(balance=Decimal("100"))

    def test_initialization(self) -> None:
        """Test l'initialisation de la stratégie adaptative."""
        rules = [
            StrategyRule(
                condition=SwitchCondition.CONSECUTIVE_LOSSES,
                threshold=3,
                target_strategy="fibonacci",
            )
        ]

        config = AdaptiveConfig(base_bet=Decimal("0.001"), initial_strategy="flat", rules=rules)

        adaptive = AdaptiveStrategy(config)

        assert adaptive.initial_strategy == "flat"
        assert adaptive.current_strategy_name == "flat"
        assert len(adaptive.rules) == 1
        assert adaptive.current_strategy is not None

    def test_initial_strategy_creation(self) -> None:
        """Test la création de la stratégie initiale."""
        config = AdaptiveConfig(
            base_bet=Decimal("0.001"),
            initial_strategy="martingale",
            initial_config={"max_losses": 10},
        )

        adaptive = AdaptiveStrategy(config)

        assert adaptive.current_strategy_name == "martingale"
        assert adaptive.current_strategy.config.max_losses == 10

    def test_calculate_next_bet_delegates(self) -> None:
        """Test que calculate_next_bet délègue à la stratégie courante."""
        config = AdaptiveConfig(base_bet=Decimal("0.001"), initial_strategy="flat")

        adaptive = AdaptiveStrategy(config)
        decision = adaptive.calculate_next_bet(self.game_state)

        # Flat betting devrait retourner base_bet
        assert decision == Decimal("0.001")

    def test_consecutive_losses_switch(self) -> None:
        """Test le changement après pertes consécutives."""
        rules = [
            StrategyRule(
                condition=SwitchCondition.CONSECUTIVE_LOSSES,
                threshold=2,
                target_strategy="fibonacci",
            )
        ]

        config = AdaptiveConfig(
            base_bet=Decimal("0.001"),
            initial_strategy="flat",
            rules=rules,
            min_bets_before_switch=1,
        )

        adaptive = AdaptiveStrategy(config)

        # État initial
        assert adaptive.current_strategy_name == "flat"

        # Première perte
        loss_result = BetResult(
            amount=Decimal("0.001"),
            won=False,
            multiplier=2.0,
            roll=60.0,
            threshold=49.5,
            payout=Decimal("0"),
        )

        self.game_state.consecutive_losses = 1
        adaptive.update_after_result(loss_result)
        # Calculer le prochain bet pour déclencher la vérification des conditions
        adaptive.calculate_next_bet(self.game_state)
        assert adaptive.current_strategy_name == "flat"  # Pas encore de changement

        # Deuxième perte - devrait déclencher le changement
        self.game_state.consecutive_losses = 2
        adaptive.update_after_result(loss_result)
        # Calculer le prochain bet pour déclencher la vérification des conditions
        adaptive.calculate_next_bet(self.game_state)
        assert adaptive.current_strategy_name == "fibonacci"

    def test_consecutive_wins_switch(self) -> None:
        """Test le changement après gains consécutifs."""
        rules = [
            StrategyRule(
                condition=SwitchCondition.CONSECUTIVE_WINS,
                threshold=3,
                target_strategy="paroli",
            )
        ]

        config = AdaptiveConfig(
            base_bet=Decimal("0.001"),
            initial_strategy="flat",
            rules=rules,
            min_bets_before_switch=1,
        )

        adaptive = AdaptiveStrategy(config)

        win_result = BetResult(
            amount=Decimal("0.001"),
            won=True,
            multiplier=2.0,
            roll=30.0,
            threshold=49.5,
            payout=Decimal("0.002"),
        )

        # Simuler 3 gains consécutifs
        for i in range(1, 4):
            self.game_state.consecutive_wins = i
            adaptive.update_after_result(win_result)
            adaptive.calculate_next_bet(self.game_state)

            if i < 3:
                assert adaptive.current_strategy_name == "flat"
            else:
                assert adaptive.current_strategy_name == "paroli"

    def test_drawdown_threshold_switch(self) -> None:
        """Test le changement basé sur le drawdown."""
        rules = [
            StrategyRule(
                condition=SwitchCondition.DRAWDOWN_THRESHOLD,
                threshold=0.1,  # 10% drawdown
                target_strategy="flat",
            )
        ]

        config = AdaptiveConfig(
            base_bet=Decimal("0.001"),
            initial_strategy="martingale",
            rules=rules,
            min_bets_before_switch=1,
        )

        adaptive = AdaptiveStrategy(config)

        # Initialiser le peak_balance en appelant calculate_next_bet d'abord
        adaptive.calculate_next_bet(self.game_state)

        # Maintenant simuler un gros drawdown
        self.game_state.balance = Decimal("85")  # 15% de perte depuis 100

        loss_result = BetResult(
            amount=Decimal("0.001"),
            won=False,
            multiplier=2.0,
            roll=60.0,
            threshold=49.5,
            payout=Decimal("0"),
        )

        adaptive.update_after_result(loss_result)
        adaptive.calculate_next_bet(self.game_state)

        # Devrait passer à flat pour la sécurité
        assert adaptive.current_strategy_name == "flat"

    def test_low_confidence_switch(self) -> None:
        """Test le changement basé sur une faible confiance."""
        rules = [
            StrategyRule(
                condition=SwitchCondition.LOW_CONFIDENCE,
                threshold=0.3,  # Confiance < 30%
                target_strategy="flat",
            )
        ]

        config = AdaptiveConfig(
            base_bet=Decimal("0.001"),
            initial_strategy="martingale",
            rules=rules,
            min_bets_before_switch=1,
        )

        adaptive = AdaptiveStrategy(config)

        # Forcer une faible confiance
        adaptive.current_strategy.confidence = 0.2

        loss_result = BetResult(
            amount=Decimal("0.001"),
            won=False,
            multiplier=2.0,
            roll=60.0,
            threshold=49.5,
            payout=Decimal("0"),
        )

        adaptive.update_after_result(loss_result)
        adaptive.calculate_next_bet(self.game_state)
        assert adaptive.current_strategy_name == "flat"

    def test_balance_threshold_switch(self) -> None:
        """Test le changement basé sur le solde."""
        rules = [
            StrategyRule(
                condition=SwitchCondition.BALANCE_THRESHOLD,
                threshold=50,  # Solde < 50
                target_strategy="flat",
            )
        ]

        config = AdaptiveConfig(
            base_bet=Decimal("0.001"),
            initial_strategy="martingale",
            rules=rules,
            min_bets_before_switch=1,
        )

        adaptive = AdaptiveStrategy(config)

        # Simuler un solde bas
        self.game_state.balance = Decimal("40")

        loss_result = BetResult(
            amount=Decimal("0.001"),
            won=False,
            multiplier=2.0,
            roll=60.0,
            threshold=49.5,
            payout=Decimal("0"),
        )

        adaptive.update_after_result(loss_result)
        adaptive.calculate_next_bet(self.game_state)
        assert adaptive.current_strategy_name == "flat"

    def test_cooldown_prevents_immediate_switch(self) -> None:
        """Test que le cooldown empêche un changement immédiat."""
        rules = [
            StrategyRule(
                condition=SwitchCondition.CONSECUTIVE_LOSSES,
                threshold=1,
                target_strategy="fibonacci",
                cooldown_bets=5,
            ),
            StrategyRule(
                condition=SwitchCondition.CONSECUTIVE_LOSSES,
                threshold=1,
                target_strategy="martingale",
                cooldown_bets=5,
            ),
        ]

        config = AdaptiveConfig(
            base_bet=Decimal("0.001"),
            initial_strategy="flat",
            rules=rules,
            min_bets_before_switch=1,
        )

        adaptive = AdaptiveStrategy(config)

        loss_result = BetResult(
            amount=Decimal("0.001"),
            won=False,
            multiplier=2.0,
            roll=60.0,
            threshold=49.5,
            payout=Decimal("0"),
        )

        # Premier changement
        self.game_state.consecutive_losses = 1
        adaptive.update_after_result(loss_result)
        adaptive.calculate_next_bet(self.game_state)
        assert adaptive.current_strategy_name == "fibonacci"

        # Deuxième changement immédiat - devrait être bloqué par cooldown
        adaptive.update_after_result(loss_result)
        adaptive.calculate_next_bet(self.game_state)
        assert adaptive.current_strategy_name == "fibonacci"  # Pas de changement

    def test_min_bets_before_switch(self) -> None:
        """Test le minimum de paris avant changement."""
        rules = [
            StrategyRule(
                condition=SwitchCondition.CONSECUTIVE_LOSSES,
                threshold=1,
                target_strategy="fibonacci",
            )
        ]

        config = AdaptiveConfig(
            base_bet=Decimal("0.001"),
            initial_strategy="flat",
            rules=rules,
            min_bets_before_switch=3,
        )

        adaptive = AdaptiveStrategy(config)

        loss_result = BetResult(
            amount=Decimal("0.001"),
            won=False,
            multiplier=2.0,
            roll=60.0,
            threshold=49.5,
            payout=Decimal("0"),
        )

        # Premier pari - pas de changement
        self.game_state.consecutive_losses = 1
        adaptive.bets_since_switch = 1
        adaptive.update_after_result(loss_result)
        adaptive.calculate_next_bet(self.game_state)
        assert adaptive.current_strategy_name == "flat"

        # Troisième pari - maintenant peut changer
        adaptive.bets_since_switch = 3
        adaptive.update_after_result(loss_result)
        adaptive.calculate_next_bet(self.game_state)
        assert adaptive.current_strategy_name == "fibonacci"

    def test_reset_state(self) -> None:
        """Test la réinitialisation de l'état."""
        rules = [
            StrategyRule(
                condition=SwitchCondition.CONSECUTIVE_LOSSES,
                threshold=2,
                target_strategy="fibonacci",
            )
        ]

        config = AdaptiveConfig(base_bet=Decimal("0.001"), initial_strategy="flat", rules=rules)

        adaptive = AdaptiveStrategy(config)

        # Changer l'état
        adaptive.current_strategy_name = "fibonacci"
        adaptive.bets_since_switch = 10
        adaptive.bets_in_current_strategy = 10
        adaptive.last_switch_bet = 5

        # Réinitialiser
        adaptive.reset_state()

        assert adaptive.current_strategy_name == "flat"
        assert adaptive.bets_in_current_strategy == 0
        assert adaptive.last_switch_bet == 0

    def test_get_name(self) -> None:
        """Test le nom de la stratégie."""
        config = AdaptiveConfig(base_bet=Decimal("0.001"), initial_strategy="flat")

        adaptive = AdaptiveStrategy(config)
        name = adaptive.get_name()

        assert "Adaptive" in name
        assert "flat" in name
