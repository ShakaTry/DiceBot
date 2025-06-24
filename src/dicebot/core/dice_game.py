import random
from decimal import Decimal

from .constants import MAX_MULTIPLIER, MIN_MULTIPLIER
from .models import BetResult, BetType, GameConfig
from .provably_fair import ProvablyFairGenerator


class DiceGame:
    def __init__(
        self,
        config: GameConfig | None = None,
        seed: int | None = None,
        use_provably_fair: bool = True,
        server_seed: str | None = None,
        client_seed: str | None = None,
    ):
        """
        Initialise le jeu de dés.

        Args:
            config: Configuration du jeu
            seed: Seed pour mode test (legacy)
            use_provably_fair: Utiliser le système provably fair (défaut: True)
            server_seed: Server seed spécifique (optionnel)
            client_seed: Client seed spécifique (optionnel)
        """
        self.config = config or GameConfig()
        self.house_edge = self.config.house_edge

        # Mode provably fair (mode normal)
        if use_provably_fair:
            self.provably_fair = ProvablyFairGenerator(server_seed, client_seed)
            self.rng = None  # Pas utilisé en mode provably fair
        else:
            # Mode legacy pour tests
            self.rng = random.Random(seed)
            self.provably_fair = None

    def calculate_win_chance(self, target: float, bet_type: BetType) -> float:
        """Calcule la probabilité de gagner selon le target et le type de pari."""
        if target < 0.01 or target > 99.99:
            raise ValueError("Target must be between 0.01 and 99.99")

        if bet_type == BetType.UNDER:
            # Gagner si roll < target
            raw_chance = target
        else:  # BetType.OVER
            # Gagner si roll > target
            raw_chance = 100.0 - target

        # Apply house edge
        actual_chance = raw_chance * (1 - self.house_edge)
        return actual_chance

    def calculate_win_chance_from_multiplier(self, multiplier: float) -> float:
        """Méthode legacy pour compatibilité - calcule via multiplier."""
        if multiplier < MIN_MULTIPLIER or multiplier > MAX_MULTIPLIER:
            raise ValueError(
                f"Multiplier must be between {MIN_MULTIPLIER} and {MAX_MULTIPLIER}"
            )

        # Win chance without house edge
        raw_chance = 100.0 / multiplier

        # Apply house edge
        actual_chance = raw_chance * (1 - self.house_edge)

        return actual_chance

    def target_from_multiplier(
        self, multiplier: float, bet_type: BetType = BetType.UNDER
    ) -> float:
        """Convertit un multiplicateur en target selon le type de pari."""
        # Win chance raw (sans house edge)
        win_chance_raw = 100.0 / multiplier

        if bet_type == BetType.UNDER:
            # Pour UNDER, target = win_chance_raw
            target = win_chance_raw
        else:  # BetType.OVER
            # Pour OVER, target = 100 - win_chance_raw
            target = 100.0 - win_chance_raw

        # Clamp entre 0.01 et 99.99
        return max(0.01, min(99.99, target))

    def multiplier_from_target(self, target: float, bet_type: BetType) -> float:
        """Convertit un target en multiplicateur selon le type de pari."""
        win_chance = self.calculate_win_chance(target, bet_type)

        if win_chance <= 0:
            return MAX_MULTIPLIER

        # Multiplier = 100 / win_chance_raw
        win_chance_raw = win_chance / (1 - self.house_edge)
        multiplier = 100.0 / win_chance_raw

        return max(MIN_MULTIPLIER, min(MAX_MULTIPLIER, multiplier))

    def calculate_threshold(self, target: float, bet_type: BetType) -> float:
        """Calcule le seuil de victoire - pour compatibilité, retourne le target."""
        return target

    def roll(
        self, bet_amount: Decimal, target: float, bet_type: BetType = BetType.UNDER
    ) -> BetResult:
        """
        Lance un dé avec le montant, target et type donnés.

        Args:
            bet_amount: Montant du pari
            target: Nombre cible (0.01-99.99)
            bet_type: Type de pari (UNDER ou OVER)

        Returns:
            Résultat du pari avec informations provably fair et OVER/UNDER
        """
        if bet_amount < self.config.min_bet_ltc:
            raise ValueError(f"Minimum bet is {self.config.min_bet_ltc} LTC")

        if bet_amount > self.config.max_bet_ltc:
            raise ValueError(f"Maximum bet is {self.config.max_bet_ltc} LTC")

        if target < 0.01 or target > 99.99:
            raise ValueError("Target must be between 0.01 and 99.99")

        # Calculer le multiplicateur et la condition de victoire
        multiplier = self.multiplier_from_target(target, bet_type)
        threshold = self.calculate_threshold(target, bet_type)

        # Générer le résultat selon le mode
        if self.provably_fair:
            # Mode provably fair (normal)
            seed_info = self.provably_fair.get_current_seed_info()
            roll_value = self.provably_fair.generate_dice_result()

            # Déterminer la victoire selon le type de pari
            if bet_type == BetType.UNDER:
                won = roll_value < target
            else:  # BetType.OVER
                won = roll_value > target

            # Créer le résultat avec infos de seed et OVER/UNDER
            result = BetResult(
                roll=roll_value,
                won=won,
                threshold=threshold,
                amount=bet_amount,
                payout=bet_amount * Decimal(str(multiplier)) if won else Decimal("0"),
                multiplier=multiplier,
                bet_type=bet_type,
                target=target,
                server_seed_hash=seed_info["server_seed_hash"],
                client_seed=seed_info["client_seed"],
                nonce=seed_info["nonce"]
                - 1,  # Le nonce a été incrémenté dans generate_dice_result
            )
        else:
            # Mode legacy pour tests
            roll_value = self.rng.random() * 100

            # Déterminer la victoire selon le type de pari
            if bet_type == BetType.UNDER:
                won = roll_value < target
            else:  # BetType.OVER
                won = roll_value > target

            result = BetResult(
                roll=roll_value,
                won=won,
                threshold=threshold,
                amount=bet_amount,
                payout=bet_amount * Decimal(str(multiplier)) if won else Decimal("0"),
                multiplier=multiplier,
                bet_type=bet_type,
                target=target,
            )

        return result

    def roll_legacy(self, bet_amount: Decimal, multiplier: float) -> BetResult:
        """
        Méthode legacy pour compatibilité avec l'ancien système basé sur multiplicateur.
        Utilise UNDER par défaut.
        """
        target = self.target_from_multiplier(multiplier, BetType.UNDER)
        return self.roll(bet_amount, target, BetType.UNDER)

    def expected_value(
        self, bet_amount: Decimal, target: float, bet_type: BetType
    ) -> Decimal:
        """Calcule la valeur attendue d'un pari OVER/UNDER."""
        win_chance = self.calculate_win_chance(target, bet_type) / 100
        multiplier = self.multiplier_from_target(target, bet_type)
        expected_win = bet_amount * Decimal(str(multiplier)) * Decimal(str(win_chance))
        return expected_win - bet_amount

    def expected_value_legacy(self, bet_amount: Decimal, multiplier: float) -> Decimal:
        """Méthode legacy pour compatibilité."""
        win_chance = self.calculate_win_chance_from_multiplier(multiplier) / 100
        expected_win = bet_amount * Decimal(str(multiplier)) * Decimal(str(win_chance))
        return expected_win - bet_amount

    def kelly_criterion(
        self, bankroll: Decimal, target: float, bet_type: BetType
    ) -> Decimal:
        """Calcule le critère de Kelly pour un pari OVER/UNDER."""
        win_prob = self.calculate_win_chance(target, bet_type) / 100
        lose_prob = 1 - win_prob
        multiplier = self.multiplier_from_target(target, bet_type)

        b = multiplier - 1  # Net odds received on the bet

        # Kelly formula: f = (bp - q) / b
        # where f = fraction of bankroll to bet
        # b = net odds, p = win probability, q = lose probability
        kelly_fraction = (b * win_prob - lose_prob) / b

        # Kelly can be negative (don't bet) or > 1 (impossible)
        if kelly_fraction <= 0:
            return Decimal("0")

        # Apply Kelly fraction to bankroll
        # Usually we use fractional Kelly (e.g., 0.25 * kelly) for safety
        safe_kelly = min(kelly_fraction * 0.25, 0.1)  # Max 10% of bankroll

        return bankroll * Decimal(str(safe_kelly))

    def kelly_criterion_legacy(self, bankroll: Decimal, multiplier: float) -> Decimal:
        """Méthode legacy pour compatibilité."""
        win_prob = self.calculate_win_chance_from_multiplier(multiplier) / 100
        lose_prob = 1 - win_prob

        b = multiplier - 1  # Net odds received on the bet

        # Kelly formula: f = (bp - q) / b
        # where f = fraction of bankroll to bet
        # b = net odds, p = win probability, q = lose probability
        kelly_fraction = (b * win_prob - lose_prob) / b

        # Kelly can be negative (don't bet) or > 1 (impossible)
        if kelly_fraction <= 0:
            return Decimal("0")

        # Apply Kelly fraction to bankroll
        # Usually we use fractional Kelly (e.g., 0.25 * kelly) for safety
        safe_kelly = min(kelly_fraction * 0.25, 0.1)  # Max 10% of bankroll

        return bankroll * Decimal(str(safe_kelly))

    # === Méthodes Provably Fair ===

    def set_client_seed(self, client_seed: str) -> None:
        """
        Change le client seed.

        Args:
            client_seed: Nouveau client seed
        """
        if not self.provably_fair:
            raise RuntimeError("Provably fair mode not enabled")

        self.provably_fair.set_client_seed(client_seed)

    def rotate_seeds(self) -> dict[str, str | int] | None:
        """
        Effectue une rotation des seeds (révèle l'ancien server seed).

        Returns:
            Informations de l'ancien seed pour vérification, ou None si mode legacy
        """
        if not self.provably_fair:
            return None

        old_seeds = self.provably_fair.rotate_seeds()
        return {
            "server_seed": old_seeds.server_seed,
            "server_seed_hash": old_seeds.server_seed_hash,
            "client_seed": old_seeds.client_seed,
            "final_nonce": old_seeds.nonce,
        }

    def get_current_seed_info(self) -> dict[str, str | int] | None:
        """
        Retourne les informations publiques sur les seeds actuels.

        Returns:
            Informations de seed ou None si mode legacy
        """
        if not self.provably_fair:
            return None

        return self.provably_fair.get_current_seed_info()

    def get_verifiable_history(self) -> list[dict[str, str | int]]:
        """
        Retourne l'historique des seeds vérifiables.

        Returns:
            Liste des seeds passés avec server_seed révélé
        """
        if not self.provably_fair:
            return []

        return self.provably_fair.get_verifiable_history()

    def verify_result(self, bet_result: BetResult) -> dict[str, any] | None:
        """
        Vérifie un résultat de pari en utilisant les seeds révélés.

        Args:
            bet_result: Résultat à vérifier

        Returns:
            Détails de vérification ou None si impossible
        """
        if not self.provably_fair or not bet_result.server_seed_hash:
            return None

        # Chercher le server seed correspondant dans l'historique
        history = self.get_verifiable_history()

        for seed_info in history:
            if seed_info["server_seed_hash"] == bet_result.server_seed_hash:
                # Utiliser BitslerVerifier pour vérifier
                from .provably_fair import BitslerVerifier

                return BitslerVerifier.verify_dice_result(
                    seed_info["server_seed"],
                    bet_result.client_seed,
                    bet_result.nonce,
                    bet_result.roll,
                )

        return {
            "error": "Server seed not found in verifiable history",
            "available_seeds": len(history),
        }

    @property
    def is_provably_fair_enabled(self) -> bool:
        """Retourne True si le mode provably fair est activé."""
        return self.provably_fair is not None
