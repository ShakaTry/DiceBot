"""
Système Provably Fair compatible avec Bitsler.com

Implémente l'algorithme exact utilisé par Bitsler pour générer des résultats
vérifiables et transparents dans les jeux de dés.
"""

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from typing import Any


@dataclass
class SeedData:
    """Données de seed pour un système provably fair."""

    server_seed: str
    client_seed: str
    nonce: int = 0

    @property
    def server_seed_hash(self) -> str:
        """Hash du server seed (visible publiquement)."""
        return hashlib.sha256(self.server_seed.encode()).hexdigest()


class ProvablyFairGenerator:
    """
    Générateur provably fair compatible avec Bitsler.

    Utilise l'algorithme exact de Bitsler :
    1. HMAC-SHA512(server_seed, client_seed + "," + nonce)
    2. Extraction de chunks de 5 hex jusqu'à nombre <= 999999
    3. Modulo 10000 et division par 100 pour le résultat dice
    """

    def __init__(self, server_seed: str | None = None, client_seed: str | None = None) -> None:
        """
        Initialise le générateur.

        Args:
            server_seed: Seed serveur (généré automatiquement si None)
            client_seed: Seed client (généré automatiquement si None)
        """
        self.current_seeds = SeedData(
            server_seed=server_seed or self._generate_server_seed(),
            client_seed=client_seed or self._generate_client_seed(),
            nonce=0,
        )

        # Historique des seeds pour vérification
        self.seed_history: list[SeedData] = []

    def _generate_server_seed(self) -> str:
        """Génère un server seed cryptographiquement sécurisé."""
        return secrets.token_hex(32)  # 64 caractères hex

    def _generate_client_seed(self) -> str:
        """Génère un client seed par défaut."""
        return secrets.token_hex(16)  # 32 caractères hex

    def set_client_seed(self, client_seed: str) -> None:
        """
        Change le client seed.

        Args:
            client_seed: Nouveau client seed
        """
        if len(client_seed.strip()) == 0:
            raise ValueError("Client seed cannot be empty")

        self.current_seeds.client_seed = client_seed.strip()

    def rotate_seeds(self) -> SeedData:
        """
        Rotate les seeds (comme sur Bitsler).

        Sauvegarde les seeds actuels dans l'historique et génère de nouveaux seeds.

        Returns:
            Les anciens seeds pour vérification
        """
        old_seeds = SeedData(
            server_seed=self.current_seeds.server_seed,
            client_seed=self.current_seeds.client_seed,
            nonce=self.current_seeds.nonce,
        )

        # Sauvegarder pour l'historique
        self.seed_history.append(old_seeds)

        # Générer de nouveaux seeds
        self.current_seeds = SeedData(
            server_seed=self._generate_server_seed(),
            client_seed=self.current_seeds.client_seed,  # Garder le même client seed
            nonce=0,
        )

        return old_seeds

    def generate_dice_result(self) -> float:
        """
        Génère un résultat de dés selon l'algorithme Bitsler.

        Returns:
            Résultat entre 0.00 et 99.99
        """
        # Algorithme exact de Bitsler
        message = f"{self.current_seeds.client_seed},{self.current_seeds.nonce}"
        seed_hash = hmac.new(
            self.current_seeds.server_seed.encode(), message.encode(), hashlib.sha512
        ).hexdigest()

        # Extraire un nombre <= 999999
        number = self._extract_valid_number(seed_hash)

        # Calculer le résultat dice : (number % 10000) / 100
        dice_result = (number % 10000) / 100

        # Incrémenter le nonce
        self.current_seeds.nonce += 1

        return dice_result

    def _extract_valid_number(self, seed_hash: str) -> int:
        """
        Extrait un nombre valide (<= 999999) du hash selon l'algorithme Bitsler.

        Args:
            seed_hash: Hash SHA512 en hexadécimal

        Returns:
            Nombre entre 0 et 999999
        """
        offset = 0

        while offset + 5 <= len(seed_hash):
            # Prendre 5 caractères hex
            hex_chunk = seed_hash[offset : offset + 5]
            number = int(hex_chunk, 16)

            if number <= 999999:
                return number

            offset += 5

        # Fallback : si aucun chunk valide trouvé, utiliser les 5 premiers modulo
        fallback_chunk = seed_hash[:5]
        return int(fallback_chunk, 16) % 1000000

    def verify_result(
        self, server_seed: str, client_seed: str, nonce: int, expected_result: float
    ) -> bool:
        """
        Vérifie un résultat avec les seeds donnés.

        Args:
            server_seed: Server seed révélé
            client_seed: Client seed utilisé
            nonce: Nonce utilisé
            expected_result: Résultat attendu

        Returns:
            True si le résultat est correct
        """
        message = f"{client_seed},{nonce}"
        seed_hash = hmac.new(server_seed.encode(), message.encode(), hashlib.sha512).hexdigest()

        number = self._extract_valid_number(seed_hash)
        calculated_result = (number % 10000) / 100

        # Tolérance pour les erreurs de floating point
        return abs(calculated_result - expected_result) < 0.005

    def get_current_seed_info(self) -> dict[str, str | int]:
        """
        Retourne les informations publiques sur les seeds actuels.

        Returns:
            Dictionnaire avec server_seed_hash, client_seed, nonce
        """
        return {
            "server_seed_hash": self.current_seeds.server_seed_hash,
            "client_seed": self.current_seeds.client_seed,
            "nonce": self.current_seeds.nonce,
        }

    def get_verifiable_history(self) -> list[dict[str, str | int]]:
        """
        Retourne l'historique des seeds vérifiables.

        Returns:
            Liste des seeds passés avec server_seed révélé
        """
        return [
            {
                "server_seed": seed.server_seed,
                "server_seed_hash": seed.server_seed_hash,
                "client_seed": seed.client_seed,
                "final_nonce": seed.nonce,
            }
            for seed in self.seed_history
        ]


class BitslerVerifier:
    """Utilitaire de vérification des résultats Bitsler."""

    @staticmethod
    def verify_dice_result(
        server_seed: str, client_seed: str, nonce: int, expected_result: float
    ) -> dict[str, Any]:
        """
        Vérifie un résultat de dés avec les paramètres donnés.

        Args:
            server_seed: Server seed révélé
            client_seed: Client seed utilisé
            nonce: Nonce du pari
            expected_result: Résultat attendu

        Returns:
            Dictionnaire avec les détails de vérification
        """
        # Recalculer le résultat
        message = f"{client_seed},{nonce}"
        seed_hash = hmac.new(server_seed.encode(), message.encode(), hashlib.sha512).hexdigest()

        # Extraire le nombre valide
        generator = ProvablyFairGenerator()
        # Access private method for verification
        number = generator._extract_valid_number(seed_hash)  # noqa: SLF001
        calculated_result = (number % 10000) / 100

        # Vérifier
        is_valid = abs(calculated_result - expected_result) < 0.005

        return {
            "server_seed": server_seed,
            "client_seed": client_seed,
            "nonce": nonce,
            "message": message,
            "hmac_sha512": seed_hash,
            "extracted_number": number,
            "calculated_result": calculated_result,
            "expected_result": expected_result,
            "is_valid": is_valid,
            "difference": abs(calculated_result - expected_result),
        }

    @staticmethod
    def batch_verify(results: list[dict]) -> dict[str, Any]:
        """
        Vérifie une liste de résultats en batch.

        Args:
            results: Liste de dicts avec server_seed, client_seed, nonce, result

        Returns:
            Statistiques de vérification
        """
        total = len(results)
        valid = 0
        invalid_results = []

        for i, result in enumerate(results):
            verification = BitslerVerifier.verify_dice_result(
                result["server_seed"],
                result["client_seed"],
                result["nonce"],
                result["result"],
            )

            if verification["is_valid"]:
                valid += 1
            else:
                invalid_results.append({"index": i, "verification": verification})

        return {
            "total_results": total,
            "valid_results": valid,
            "invalid_results": len(invalid_results),
            "success_rate": valid / total if total > 0 else 0,
            "invalid_details": invalid_results,
        }
