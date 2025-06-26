"""
Tests pour les contraintes du système Provably Fair.

Vérifie que le système respecte la contrainte fondamentale où chaque nonce
doit être utilisé séquentiellement et ne peut pas être skippé.
"""

from decimal import Decimal
from typing import Any
from unittest.mock import Mock, patch

from dicebot.core.dice_game import DiceGame
from dicebot.core.models import BetDecision, BetType, GameState
from dicebot.simulation.engine import SimulationEngine
from dicebot.strategies.factory import StrategyConfig
from dicebot.strategies.martingale import MartingaleStrategy
from dicebot.strategies.parking import ParkingConfig, ParkingStrategy


class TestProvablyFairConstraints:
    """Test les contraintes du système Provably Fair."""

    def test_nonce_must_be_sequential(self) -> None:
        """Vérifie que les nonces sont utilisés séquentiellement."""
        game: DiceGame = DiceGame(use_provably_fair=True)

        # Vérifier nonce initial
        assert game.provably_fair is not None
        assert game.provably_fair.current_seeds.nonce == 0

        # Premier pari - nonce 0
        game.roll(Decimal("0.001"), 50.0)
        assert game.provably_fair.current_seeds.nonce == 1

        # Deuxième pari - nonce 1
        game.roll(Decimal("0.001"), 50.0)
        assert game.provably_fair.current_seeds.nonce == 2

        # On ne peut pas skip - chaque roll incrémente le nonce
        for _i in range(10):
            game.roll(Decimal("0.001"), 50.0)
        assert game.provably_fair.current_seeds.nonce == 12

    def test_seed_rotation_resets_nonce(self) -> None:
        """Vérifie que la rotation de seed reset le nonce à 0."""
        game: DiceGame = DiceGame(use_provably_fair=True)

        # Faire quelques paris
        for _ in range(5):
            game.roll(Decimal("0.001"), 50.0)
        assert game.provably_fair is not None
        assert game.provably_fair.current_seeds.nonce == 5

        # Rotation de seed
        old_seeds: dict[str, Any] = game.rotate_seeds() or {}
        assert old_seeds["final_nonce"] == 5
        assert game.provably_fair.current_seeds.nonce == 0

    def test_parking_strategy_toggle_bet_type(self) -> None:
        """Vérifie que toggle UNDER/OVER ne consomme pas de nonce."""
        config: ParkingConfig = ParkingConfig(base_bet=Decimal("0.001"))
        parking: ParkingStrategy = ParkingStrategy(config)
        game_state: GameState = GameState(balance=Decimal("100"))

        # Forcer le mode parking
        game_state.consecutive_losses = 6  # > 5

        # Premier appel - devrait toggle
        decision: BetDecision = parking.decide_bet(game_state)
        assert decision.skip is True
        assert decision.action == "toggle_bet_type"

        # Vérifier qu'on peut toggle plusieurs fois
        for _i in range(2):
            decision = parking.decide_bet(game_state)
            assert decision.action == "toggle_bet_type"

        # Après max toggles, devrait forcer un pari
        decision = parking.decide_bet(game_state)
        assert decision.action == "forced_parking_bet"
        assert decision.amount == parking.config.parking_bet_amount

    def test_parking_strategy_seed_rotation(self) -> None:
        """Vérifie que la stratégie peut demander une rotation de seed."""
        config: ParkingConfig = ParkingConfig(
            base_bet=Decimal("0.001"),
            auto_seed_rotation_after=100,
            seed_rotation_on_losses=3,
            parking_on_consecutive_losses=1,  # Set low to activate parking easily
        )
        parking: ParkingStrategy = ParkingStrategy(config)
        game_state: GameState = GameState(balance=Decimal("100"))

        # Cas 1: Rotation après beaucoup de nonces
        game_state.metadata["current_nonce"] = 101
        game_state.consecutive_losses = 1  # Activer parking

        decision: BetDecision = parking.decide_bet(game_state)
        assert decision.action == "change_seed"

        # Cas 2: Rotation après pertes consécutives
        game_state.metadata["current_nonce"] = 50
        game_state.consecutive_losses = 3

        decision: BetDecision = parking.decide_bet(game_state)
        assert decision.action == "change_seed"

    def test_forced_parking_bet_tracking(self) -> None:
        """Vérifie que les paris parking sont trackés correctement."""
        from dicebot.core.models import BetResult
        from dicebot.money.vault import Vault, VaultConfig

        # Setup
        vault_config: VaultConfig = VaultConfig(total_capital=Decimal("100"))
        _vault: Vault = Vault(vault_config)
        _engine: SimulationEngine = SimulationEngine(vault_config)

        # Stratégie parking avec seed rotation désactivée
        config: ParkingConfig = ParkingConfig(
            base_bet=Decimal("0.001"),
            seed_rotation_on_losses=20,  # Set high to prevent seed rotation
        )
        parking: ParkingStrategy = ParkingStrategy(config)
        parking.is_parking = True
        parking.toggles_count = 3  # Force un pari parking

        # Mock game state
        game_state: GameState = GameState(balance=Decimal("10"))
        game_state.consecutive_losses = 10  # Below seed_rotation_on_losses

        # Décision forcée
        decision: BetDecision = parking.decide_bet(game_state)
        assert decision.action == "forced_parking_bet"

        # Simuler le résultat
        result: BetResult = BetResult(
            multiplier=99.0,
            roll=98.5,
            won=False,  # Perte parking (1% chance)
            threshold=98.0,
            amount=decision.amount,
            payout=Decimal("0"),
            bet_type=BetType.UNDER,
            target=98.0,
        )

        # Mettre à jour le game state manuellement (comme le ferait l'engine)
        # Note: decide_bet() a déjà incrémenté parking_bets_count
        if decision.action == "forced_parking_bet":
            if not result.won:
                game_state.parking_losses += result.amount

        assert game_state.parking_bets_count == 1
        assert game_state.parking_losses == decision.amount

    def test_simulation_engine_handles_actions(self) -> None:
        """Vérifie que SimulationEngine gère correctement les actions."""
        from dicebot.money.vault import VaultConfig

        vault_config: VaultConfig = VaultConfig(total_capital=Decimal("100"))
        engine: SimulationEngine = SimulationEngine(vault_config)

        # Mock strategy qui demande des actions
        mock_strategy: Mock = Mock()
        mock_strategy.reset_state = Mock()
        mock_strategy.update_after_result = Mock()

        # Séquence d'actions
        actions: list[BetDecision] = [
            BetDecision(
                amount=Decimal("0"),
                multiplier=2.0,
                skip=True,
                action="toggle_bet_type",
                bet_type=BetType.OVER,
            ),
            BetDecision(amount=Decimal("0"), multiplier=2.0, skip=True, action="change_seed"),
            BetDecision(amount=Decimal("0.001"), multiplier=2.0, skip=False, action=None),
        ]

        mock_strategy.decide_bet = Mock(side_effect=actions)

        # Run session (limité)
        session_config: dict[str, Any] = {"max_bets": 1}
        with patch.object(engine.dice_game, "rotate_seeds") as mock_rotate:
            session = engine.run_session(mock_strategy, session_config)

            # Vérifier que rotate_seeds a été appelé
            mock_rotate.assert_called_once()

        # Vérifier les métriques
        assert session.game_state.bet_type_toggles == 1
        assert session.game_state.seed_rotations_count == 1

    def test_no_skip_nonce_constraint(self) -> None:
        """Vérifie qu'on ne peut pas skip de nonce dans une vraie session."""
        from dicebot.money.vault import VaultConfig
        from dicebot.strategies.flat import FlatBetting

        vault_config: VaultConfig = VaultConfig(total_capital=Decimal("100"))
        engine: SimulationEngine = SimulationEngine(vault_config)

        # Stratégie qui veut skip certains paris
        class SkipStrategy(FlatBetting):
            def __init__(self) -> None:
                config: StrategyConfig = StrategyConfig(base_bet=Decimal("0.001"))
                super().__init__(config)
                self.bet_count = 0

            def decide_bet(self, game_state: GameState) -> BetDecision:
                self.bet_count += 1
                # Essayer de skip tous les pairs
                if self.bet_count % 2 == 0:
                    return BetDecision(
                        amount=Decimal("0.001"),
                        multiplier=2.0,
                        skip=True,
                        reason="Want to skip",
                    )
                return super().decide_bet(game_state)

        strategy: SkipStrategy = SkipStrategy()
        session_config: dict[str, Any] = {"max_bets": 10}

        # Vérifier que les skips ne permettent pas de sauter des nonces
        assert engine.dice_game.provably_fair is not None
        initial_nonce: int = engine.dice_game.provably_fair.current_seeds.nonce
        session = engine.run_session(strategy, session_config)
        final_nonce: int = engine.dice_game.provably_fair.current_seeds.nonce

        # Le nombre de nonces utilisés doit correspondre aux paris réels
        # (les skips old-style ne devraient pas permettre de sauter)
        actual_bets: int = session.game_state.bets_count
        assert final_nonce - initial_nonce == actual_bets

    def test_parking_strategy_with_base_strategy(self) -> None:
        """Vérifie que ParkingStrategy peut wrapper une autre stratégie."""
        # Stratégie de base
        base_config: StrategyConfig = StrategyConfig(base_bet=Decimal("0.001"))
        base: MartingaleStrategy = MartingaleStrategy(base_config)

        # Wrapper avec parking
        parking_config: ParkingConfig = ParkingConfig(base_bet=Decimal("0.001"))
        parking: ParkingStrategy = ParkingStrategy(parking_config)
        parking.set_base_strategy(base)

        game_state: GameState = GameState(balance=Decimal("100"))

        # Mode normal - délègue à la base
        decision: BetDecision = parking.decide_bet(game_state)
        assert decision.amount == base.config.base_bet

        # Mode parking - override
        game_state.consecutive_losses = 10
        decision: BetDecision = parking.decide_bet(game_state)
        assert decision.action in [
            "toggle_bet_type",
            "change_seed",
            "forced_parking_bet",
        ]

    def test_parking_cost_calculation(self) -> None:
        """Vérifie le calcul du coût total du parking."""
        config: ParkingConfig = ParkingConfig(
            base_bet=Decimal("0.001"),
            seed_rotation_on_losses=20,  # Prevent seed rotation
            auto_seed_rotation_after=2000,  # Prevent auto rotation
        )
        parking: ParkingStrategy = ParkingStrategy(config)
        game_state: GameState = GameState(balance=Decimal("100"))

        # Forcer plusieurs paris parking
        parking.toggles_count = 3
        parking.is_parking = True  # Force parking mode
        game_state.consecutive_losses = 10

        total_parking_cost: Decimal = Decimal("0")

        for _ in range(5):
            decision: BetDecision = parking.decide_bet(game_state)
            if decision.action == "forced_parking_bet":
                # Simuler une perte (1% du temps)
                # Note: decide_bet already increments parking_bets_count
                game_state.parking_losses += decision.amount
                total_parking_cost += decision.amount

        # Vérifier que le coût est tracké
        assert game_state.parking_losses == total_parking_cost
        assert game_state.parking_bets_count == 5
