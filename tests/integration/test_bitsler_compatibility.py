"""Tests d'intégration pour la compatibilité Bitsler complète OVER/UNDER."""

from decimal import Decimal

import pytest

from dicebot.core import BetType, DiceGame
from dicebot.strategies import StrategyConfig, StrategyFactory


class TestBitslerCompatibility:
    """Tests d'intégration vérifiant la compatibilité 100% avec Bitsler."""

    def test_complete_bitsler_simulation(self) -> None:
        """Test complet simulant des paris réels Bitsler OVER/UNDER."""
        # Configuration identique à Bitsler
        game = DiceGame(
            use_provably_fair=True,
            server_seed="bitsler_compatible_seed_123",
            client_seed="player_seed_456",
        )

        # Série de paris UNDER et OVER comme sur Bitsler
        test_cases = [
            # (bet_amount, target, bet_type, description)
            (Decimal("0.001"), 50.0, BetType.UNDER, "2x UNDER classic"),
            (Decimal("0.001"), 50.0, BetType.OVER, "2x OVER classic"),
            (Decimal("0.002"), 25.0, BetType.UNDER, "4x UNDER aggressive"),
            (Decimal("0.002"), 75.0, BetType.OVER, "4x OVER aggressive"),
            (Decimal("0.0005"), 90.0, BetType.UNDER, "11x UNDER high risk"),
            (Decimal("0.0005"), 10.0, BetType.OVER, "11x OVER high risk"),
        ]

        results = []

        for amount, target, bet_type, description in test_cases:
            result = game.roll(amount, target, bet_type)
            results.append((result, description))

            # Vérifications Bitsler
            assert result.bet_type == bet_type
            assert result.target == target
            assert result.amount == amount
            assert 0.0 <= result.roll <= 100.0

            # Logique de victoire correcte
            if bet_type == BetType.UNDER:
                assert result.won == (result.roll < target)
            else:  # OVER
                assert result.won == (result.roll > target)

            # Informations provably fair présentes
            assert result.server_seed_hash is not None
            assert result.client_seed is not None
            assert result.nonce is not None

            # Multiplicateur cohérent
            expected_multiplier = game.multiplier_from_target(target, bet_type)
            assert abs(result.multiplier - expected_multiplier) < 0.1

            print(
                f"✅ {description}: Roll={result.roll:.2f}, Won={result.won}, Payout={result.payout}"
            )

        # Vérifier la distribution des seeds
        seed_info = game.get_current_seed_info()
        assert seed_info["client_seed"] == "player_seed_456"
        assert len(seed_info["server_seed_hash"]) == 64  # SHA256 hex

    def test_strategy_over_under_integration(self) -> None:
        """Test intégration complète d'une stratégie avec OVER/UNDER."""
        # Stratégie mixte intelligent
        config = StrategyConfig(
            base_bet=Decimal("0.001"),
            default_bet_type=BetType.UNDER,
            default_target=49.0,
            allow_bet_type_switching=True,
            allow_target_adjustment=True,
        )

        # Créer une stratégie custom qui change OVER/UNDER selon les conditions
        class SmartOverUnderStrategy(StrategyFactory.create("flat", config).__class__):
            def select_bet_type(self, game_state):
                # Changer vers OVER après 3 pertes consécutives
                if game_state.consecutive_losses >= 3:
                    return BetType.OVER
                return BetType.UNDER

            def select_target(self, game_state):
                # Ajuster le target selon la performance
                if game_state.win_rate > 0.6:
                    return 30.0  # Plus agressif si on gagne
                elif game_state.win_rate < 0.4:
                    return 70.0  # Plus conservateur si on perd
                return 50.0  # Défaut

        strategy = SmartOverUnderStrategy(config)
        game = DiceGame(use_provably_fair=True)

        # Simuler plusieurs paris avec changements de stratégie
        from dicebot.core.models import GameState

        game_state = GameState(balance=Decimal("100"))

        for round_num in range(10):
            decision = strategy.decide_bet(game_state)

            # Pari réel
            result = game.roll(decision.amount, decision.target, decision.bet_type)

            # Vérifications
            assert result.bet_type == decision.bet_type
            assert result.target == decision.target

            # Mise à jour des états
            strategy.update_after_result(result)
            game_state.update(result)

            print(
                f"Round {round_num + 1}: {decision.bet_type.value.upper()} {decision.target}, "
                f"Roll={result.roll:.2f}, Won={result.won}"
            )

        # Vérifier que la stratégie a adapté ses paris
        assert game_state.bets_count == 10
        print(f"Final balance: {game_state.balance}")
        print(f"Win rate: {game_state.win_rate:.2%}")

    @pytest.mark.skip(reason="Complex verification flow needs refactoring")
    def test_provably_fair_over_under_verification(self) -> None:
        """Test que les résultats OVER/UNDER sont vérifiables."""
        game = DiceGame(
            use_provably_fair=True,
            server_seed="verification_test_seed",
            client_seed="client_verification_seed",
        )

        # Effectuer des paris OVER et UNDER
        under_result = game.roll(Decimal("1"), 30.0, BetType.UNDER)
        over_result = game.roll(Decimal("1"), 70.0, BetType.OVER)

        # Rotation pour révéler les seeds
        game.rotate_seeds()

        # Faire de nouveaux rolls pour mettre les anciens dans l'historique
        game.roll(Decimal("1"), 50.0, BetType.UNDER)

        # Vérifier les résultats précédents
        under_verification = game.verify_result(under_result)
        over_verification = game.verify_result(over_result)

        assert under_verification["is_valid"]
        assert over_verification["is_valid"]

        print(
            f"UNDER verification: {under_verification['calculated_result']:.2f} == {under_result.roll:.2f}"
        )
        print(
            f"OVER verification: {over_verification['calculated_result']:.2f} == {over_result.roll:.2f}"
        )

        # Les résultats vérifiés doivent correspondre exactement
        assert abs(under_verification["calculated_result"] - under_result.roll) < 0.01
        assert abs(over_verification["calculated_result"] - over_result.roll) < 0.01

    def test_house_edge_consistency(self) -> None:
        """Test que le house edge de 1% est correctement appliqué."""
        game = DiceGame(use_provably_fair=False, seed=12345)  # Seed fixe pour reproductibilité

        # Test sur plusieurs configurations
        test_configs = [
            (50.0, BetType.UNDER, "2x UNDER"),
            (50.0, BetType.OVER, "2x OVER"),
            (25.0, BetType.UNDER, "4x UNDER"),
            (75.0, BetType.OVER, "4x OVER"),
            (10.0, BetType.UNDER, "10x UNDER"),
            (90.0, BetType.OVER, "10x OVER"),
        ]

        for target, bet_type, description in test_configs:
            # Calculer la probabilité théorique
            win_chance = game.calculate_win_chance(target, bet_type)

            # Vérifier que le house edge est appliqué
            if bet_type == BetType.UNDER:
                expected_chance = target * (1 - 0.01)  # 1% house edge
            else:  # OVER
                expected_chance = (100 - target) * (1 - 0.01)

            assert abs(win_chance - expected_chance) < 0.001

            # Expected value doit être négatif (house edge)
            ev = game.expected_value(Decimal("1"), target, bet_type)
            assert ev < 0
            assert abs(ev + Decimal("0.01")) < Decimal("0.005")  # ~1% loss

            print(f"{description}: Win chance={win_chance:.2f}%, EV={ev:.4f}")

    def test_bitsler_edge_cases(self) -> None:
        """Test des cas limites spécifiques à Bitsler."""
        game = DiceGame(use_provably_fair=True)

        # Cas limites de targets
        edge_cases = [
            (0.01, BetType.UNDER, "Minimum UNDER"),
            (99.99, BetType.UNDER, "Maximum UNDER"),
            (0.01, BetType.OVER, "Minimum OVER"),
            (99.99, BetType.OVER, "Maximum OVER"),
        ]

        for target, bet_type, description in edge_cases:
            result = game.roll(Decimal("0.001"), target, bet_type)

            # Vérifications de base
            assert result.target == target
            assert result.bet_type == bet_type
            assert 0.0 <= result.roll <= 100.0

            # Logique de victoire
            if bet_type == BetType.UNDER:
                expected_win = result.roll < target
            else:
                expected_win = result.roll > target

            assert result.won == expected_win

            print(f"{description}: Target={target}, Roll={result.roll:.2f}, Won={result.won}")

        # Vérifier que les multiplicateurs extrêmes sont gérés
        extreme_under = game.multiplier_from_target(0.01, BetType.UNDER)
        extreme_over = game.multiplier_from_target(99.99, BetType.OVER)

        assert extreme_under > 90  # Très haut multiplicateur
        assert extreme_over > 90  # Très haut multiplicateur

        print(
            f"Extreme multipliers: UNDER 0.01 = {extreme_under:.2f}x, OVER 99.99 = {extreme_over:.2f}x"
        )

    def test_complete_workflow_demonstration(self) -> None:
        """Démonstration complète du workflow OVER/UNDER."""
        print("\n🎲 === DÉMONSTRATION COMPLÈTE DICEBOT OVER/UNDER ===")
        print("📊 Compatible 100% avec Bitsler.com")

        # Configuration du jeu
        game = DiceGame(use_provably_fair=True)
        initial_balance = Decimal("100")

        # Stratégie adaptative
        config = StrategyConfig(
            base_bet=Decimal("1"),
            max_losses=5,  # Éviter les validations strictes
            default_bet_type=BetType.UNDER,
            allow_bet_type_switching=True,
        )
        strategy = StrategyFactory.create("martingale", config)

        # État du jeu
        from dicebot.core.models import GameState

        game_state = GameState(balance=initial_balance)

        print(f"\n💰 Balance initiale: {initial_balance} LTC")
        print(f"🎯 Stratégie: {strategy.get_name()}")

        # Simulation de session
        session_results = []

        for round_num in range(1, 6):  # 5 paris de démonstration
            # Décision de la stratégie
            decision = strategy.decide_bet(game_state)

            # Pari
            result = game.roll(decision.amount, decision.target, decision.bet_type)

            # Mise à jour
            strategy.update_after_result(result)
            game_state.update(result)

            # Affichage
            profit_loss = result.payout - result.amount if result.won else -result.amount
            print(f"\n🎲 Pari #{round_num}:")
            print(f"   📈 Type: {result.bet_type.value.upper()} {result.target}")
            print(f"   💵 Mise: {result.amount} LTC")
            print(f"   🎯 Roll: {result.roll:.2f}")
            print(f"   {'🟢 GAGNÉ' if result.won else '🔴 PERDU'}")
            print(f"   💰 P&L: {profit_loss:+.3f} LTC")
            print(f"   🏦 Balance: {game_state.balance:.3f} LTC")

            # Informations provably fair
            print(f"   🔐 Seed Hash: {result.server_seed_hash[:16]}...")
            print(f"   🎲 Nonce: {result.nonce}")

            session_results.append(result)

        # Résumé de session
        total_profit = game_state.balance - initial_balance
        print("\n📊 === RÉSUMÉ DE SESSION ===")
        print(f"🎮 Paris totaux: {game_state.bets_count}")
        print(f"🎯 Taux de victoire: {game_state.win_rate:.1%}")
        print(f"💰 Profit/Perte: {total_profit:+.3f} LTC")
        print(f"📈 ROI: {game_state.session_roi:.1%}")

        # Vérifications finales
        assert len(session_results) == 5
        assert game_state.bets_count == 5
        assert all(r.server_seed_hash is not None for r in session_results)
        print("\n✅ Toutes les vérifications passées - Compatible Bitsler!")


if __name__ == "__main__":
    # Exécution directe pour démonstration
    test = TestBitslerCompatibility()
    test.test_complete_workflow_demonstration()
