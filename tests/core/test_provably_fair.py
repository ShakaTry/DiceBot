"""Tests pour le système Provably Fair."""

import hashlib
import hmac
from decimal import Decimal

import pytest

from dicebot.core.dice_game import DiceGame
from dicebot.core.provably_fair import BitslerVerifier, ProvablyFairGenerator


class TestProvablyFairGenerator:
    """Test le générateur provably fair."""

    def test_initialization(self) -> None:
        """Test l'initialisation du générateur."""
        generator = ProvablyFairGenerator()

        assert generator.current_seeds.server_seed is not None
        assert generator.current_seeds.client_seed is not None
        assert generator.current_seeds.nonce == 0
        assert len(generator.seed_history) == 0

    def test_initialization_with_seeds(self) -> None:
        """Test l'initialisation avec des seeds spécifiques."""
        server_seed = "test_server_seed"
        client_seed = "test_client_seed"

        generator = ProvablyFairGenerator(server_seed, client_seed)

        assert generator.current_seeds.server_seed == server_seed
        assert generator.current_seeds.client_seed == client_seed
        assert generator.current_seeds.nonce == 0

    def test_server_seed_hash(self) -> None:
        """Test le calcul du hash du server seed."""
        server_seed = "test_server_seed"
        generator = ProvablyFairGenerator(server_seed, "client")

        expected_hash = hashlib.sha256(server_seed.encode()).hexdigest()
        assert generator.current_seeds.server_seed_hash == expected_hash

    def test_set_client_seed(self) -> None:
        """Test le changement de client seed."""
        generator = ProvablyFairGenerator()
        new_client_seed = "my_custom_seed"

        generator.set_client_seed(new_client_seed)

        assert generator.current_seeds.client_seed == new_client_seed

    def test_set_client_seed_empty_error(self) -> None:
        """Test qu'un client seed vide lève une erreur."""
        generator = ProvablyFairGenerator()

        with pytest.raises(ValueError, match="Client seed cannot be empty"):
            generator.set_client_seed("")

    def test_generate_dice_result(self) -> None:
        """Test la génération de résultats de dés."""
        generator = ProvablyFairGenerator("server123", "client456")

        # Premier résultat
        result1 = generator.generate_dice_result()
        assert 0.0 <= result1 <= 99.99
        assert generator.current_seeds.nonce == 1

        # Deuxième résultat (différent)
        result2 = generator.generate_dice_result()
        assert 0.0 <= result2 <= 99.99
        assert generator.current_seeds.nonce == 2
        assert result1 != result2  # Probabilité très faible d'avoir le même

    def test_reproducible_results(self) -> None:
        """Test que les mêmes seeds produisent les mêmes résultats."""
        server_seed = "fixed_server"
        client_seed = "fixed_client"

        # Premier générateur
        gen1 = ProvablyFairGenerator(server_seed, client_seed)
        results1 = [gen1.generate_dice_result() for _ in range(5)]

        # Deuxième générateur avec mêmes seeds
        gen2 = ProvablyFairGenerator(server_seed, client_seed)
        results2 = [gen2.generate_dice_result() for _ in range(5)]

        assert results1 == results2

    def test_rotate_seeds(self) -> None:
        """Test la rotation des seeds."""
        generator = ProvablyFairGenerator("server123", "client456")

        # Générer quelques résultats
        generator.generate_dice_result()
        generator.generate_dice_result()

        old_server = generator.current_seeds.server_seed
        old_client = generator.current_seeds.client_seed
        old_nonce = generator.current_seeds.nonce

        # Rotation
        old_seeds = generator.rotate_seeds()

        # Vérifications
        assert old_seeds.server_seed == old_server
        assert old_seeds.client_seed == old_client
        assert old_seeds.nonce == old_nonce

        # Nouveaux seeds
        assert generator.current_seeds.server_seed != old_server
        assert generator.current_seeds.client_seed == old_client  # Gardé
        assert generator.current_seeds.nonce == 0  # Reset

        # Historique
        assert len(generator.seed_history) == 1
        assert generator.seed_history[0] == old_seeds

    def test_verify_result(self) -> None:
        """Test la vérification de résultats."""
        generator = ProvablyFairGenerator("server123", "client456")

        result = generator.generate_dice_result()
        nonce = generator.current_seeds.nonce - 1  # Le nonce a été incrémenté

        # Vérification correcte
        is_valid = generator.verify_result("server123", "client456", nonce, result)
        assert is_valid

        # Vérification incorrecte
        is_invalid = generator.verify_result("wrong_server", "client456", nonce, result)
        assert not is_invalid

    def test_bitsler_algorithm_compatibility(self) -> None:
        """Test que l'algorithme est compatible avec Bitsler."""
        # Seeds connus pour test
        server_seed = "e6bbf5eda32e178e78a2c8e73b4b8bea1c17e01ac5b8e5c0d42d2a29f4b76eb7"
        client_seed = "test_client"
        nonce = 0

        # Calcul manuel selon l'algorithme Bitsler
        message = f"{client_seed},{nonce}"
        seed_hash = hmac.new(server_seed.encode(), message.encode(), hashlib.sha512).hexdigest()

        # Extraction du premier nombre valide <= 999999
        offset = 0
        while offset + 5 <= len(seed_hash):
            hex_chunk = seed_hash[offset : offset + 5]
            number = int(hex_chunk, 16)
            if number <= 999999:
                break
            offset += 5

        expected_result = (number % 10000) / 100

        # Test avec notre générateur
        generator = ProvablyFairGenerator(server_seed, client_seed)
        actual_result = generator.generate_dice_result()

        assert abs(actual_result - expected_result) < 0.005


class TestBitslerVerifier:
    """Test le vérificateur Bitsler."""

    def test_verify_dice_result(self) -> None:
        """Test la vérification d'un résultat de dés."""
        server_seed = "test_server"
        client_seed = "test_client"
        nonce = 0

        # Générer un résultat connu
        generator = ProvablyFairGenerator(server_seed, client_seed)
        expected_result = generator.generate_dice_result()

        # Vérifier
        verification = BitslerVerifier.verify_dice_result(
            server_seed, client_seed, nonce, expected_result
        )

        assert verification["is_valid"]
        assert verification["server_seed"] == server_seed
        assert verification["client_seed"] == client_seed
        assert verification["nonce"] == nonce
        assert abs(verification["calculated_result"] - expected_result) < 0.005

    def test_verify_invalid_result(self) -> None:
        """Test la vérification d'un résultat invalide."""
        verification = BitslerVerifier.verify_dice_result(
            "server",
            "client",
            0,
            99.99,  # Résultat arbitraire
        )

        # Très improbable que ce soit valide
        assert not verification["is_valid"]

    def test_batch_verify(self) -> None:
        """Test la vérification en batch."""
        server_seed = "batch_server"
        client_seed = "batch_client"

        # Générer plusieurs résultats
        generator = ProvablyFairGenerator(server_seed, client_seed)
        results = []

        for i in range(5):
            result = generator.generate_dice_result()
            results.append(
                {
                    "server_seed": server_seed,
                    "client_seed": client_seed,
                    "nonce": i,
                    "result": result,
                }
            )

        # Ajouter un résultat invalide
        results.append(
            {
                "server_seed": server_seed,
                "client_seed": client_seed,
                "nonce": 99,
                "result": 12.34,  # Arbitraire
            }
        )

        # Vérification batch
        batch_result = BitslerVerifier.batch_verify(results)

        assert batch_result["total_results"] == 6
        assert batch_result["valid_results"] == 5
        assert batch_result["invalid_results"] == 1
        assert batch_result["success_rate"] == 5 / 6


class TestDiceGameProvablyFair:
    """Test l'intégration provably fair dans DiceGame."""

    def test_dice_game_provably_fair_enabled(self) -> None:
        """Test que DiceGame utilise provably fair par défaut."""
        game = DiceGame()

        assert game.is_provably_fair_enabled
        assert game.provably_fair is not None
        assert game.rng is None

    def test_dice_game_legacy_mode(self) -> None:
        """Test le mode legacy."""
        game = DiceGame(use_provably_fair=False, seed=12345)

        assert not game.is_provably_fair_enabled
        assert game.provably_fair is None
        assert game.rng is not None

    def test_roll_with_provably_fair(self) -> None:
        """Test qu'un roll avec provably fair inclut les informations de seed."""
        game = DiceGame(server_seed="test_server", client_seed="test_client")

        # Pour un multiplier de 2.0, target = ~49.5
        result = game.roll(Decimal("1"), 49.5)

        assert result.server_seed_hash is not None
        assert result.client_seed == "test_client"
        assert result.nonce is not None
        assert 1.9 <= result.multiplier <= 2.1  # Tolérance pour house edge

    def test_set_client_seed(self) -> None:
        """Test le changement de client seed."""
        game = DiceGame(client_seed="initial")

        game.set_client_seed("new_seed")

        seed_info = game.get_current_seed_info()
        assert seed_info["client_seed"] == "new_seed"

    def test_set_client_seed_legacy_mode_error(self) -> None:
        """Test qu'on ne peut pas changer le client seed en mode legacy."""
        game = DiceGame(use_provably_fair=False)

        with pytest.raises(RuntimeError, match="Provably fair mode not enabled"):
            game.set_client_seed("test")

    def test_rotate_seeds(self) -> None:
        """Test la rotation des seeds."""
        game = DiceGame(server_seed="test_server", client_seed="test_client")

        # Faire quelques rolls
        game.roll(Decimal("1"), 2.0)
        game.roll(Decimal("1"), 2.0)

        # Rotation
        old_seeds = game.rotate_seeds()

        assert old_seeds["server_seed"] == "test_server"
        assert old_seeds["client_seed"] == "test_client"
        assert old_seeds["final_nonce"] == 2

    @pytest.mark.skip(reason="Complex verification flow needs refactoring")
    def test_verify_result(self) -> None:
        """Test la vérification d'un résultat après rotation."""
        game = DiceGame(server_seed="verify_server", client_seed="verify_client")

        # Roll, rotation et nouveau roll
        result1 = game.roll(Decimal("1"), 49.5)  # Target pour multiplier ~2.0
        game.rotate_seeds()
        game.roll(Decimal("1"), 49.5)  # Nouveau roll avec nouveaux seeds

        # Vérification du premier résultat (seeds maintenant dans l'historique)
        verification = game.verify_result(result1)

        assert verification is not None
        assert verification["is_valid"]
        assert abs(verification["calculated_result"] - result1.roll) < 0.01

    def test_reproducible_dice_game_results(self) -> None:
        """Test que DiceGame produit des résultats reproductibles."""
        server_seed = "repro_server"
        client_seed = "repro_client"

        # Premier jeu
        game1 = DiceGame(server_seed=server_seed, client_seed=client_seed)
        results1 = [game1.roll(Decimal("1"), 2.0).roll for _ in range(3)]

        # Deuxième jeu avec mêmes seeds
        game2 = DiceGame(server_seed=server_seed, client_seed=client_seed)
        results2 = [game2.roll(Decimal("1"), 2.0).roll for _ in range(3)]

        assert results1 == results2
