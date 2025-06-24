"""
Stratégie de parking pour minimiser les pertes lors des attentes forcées.

Cette stratégie gère la contrainte Provably Fair où chaque nonce doit être
utilisé séquentiellement. Elle utilise les méthodes alternatives (toggle bet type,
change seed) pour éviter de parier quand possible.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from ..core.constants import MIN_BET_LTC
from ..core.models import BetDecision, BetResult, BetType, GameState
from .base import BaseStrategy, StrategyConfig


@dataclass
class ParkingConfig(StrategyConfig):
    """Configuration pour la stratégie de parking."""

    # Configuration du parking
    parking_bet_amount: Decimal = MIN_BET_LTC
    parking_target: float = 98.0  # 99% de chance de gagner
    parking_bet_type: BetType = BetType.UNDER

    # Limites avant pari forcé
    max_toggles_before_bet: int = 3
    max_consecutive_parking_bets: int = 5

    # Conditions pour activer le parking
    parking_on_consecutive_losses: int = 5
    parking_on_drawdown_percent: float = 0.1  # 10%

    # Rotation de seed
    auto_seed_rotation_after: int = 1000  # Rotation préventive
    seed_rotation_on_losses: int = 10  # Rotation après X pertes

    def __post_init__(self):
        """Initialise les valeurs par défaut."""
        # Assurer que base_bet est défini
        if not hasattr(self, "base_bet") or self.base_bet is None:
            self.base_bet = self.parking_bet_amount


class ParkingStrategy(BaseStrategy):
    """
    Stratégie de parking intelligente.

    Minimise les pertes quand on veut attendre en utilisant :
    1. Toggle UNDER/OVER (gratuit, ne consomme pas de nonce)
    2. Rotation de seed (reset le nonce à 0)
    3. Paris minimums à haute probabilité quand forcé
    """

    def __init__(self, config: ParkingConfig | None = None):
        """Initialise la stratégie de parking."""
        # Initialiser les attributs avant d'appeler super().__init__
        self.toggles_count = 0
        self.parking_bets_count = 0
        self.last_seed_rotation_nonce = 0
        self.is_parking = False
        self.base_strategy = None

        # Maintenant appeler super().__init__ qui peut appeler reset_state()
        super().__init__(config or ParkingConfig())
        self.config: ParkingConfig = self.config

    def set_base_strategy(self, strategy: BaseStrategy) -> None:
        """Définit la stratégie de base à wrapper."""
        self.base_strategy = strategy

    def should_park(self, game_state: GameState) -> bool:
        """Détermine si on doit entrer en mode parking."""
        # Parking sur pertes consécutives
        if game_state.consecutive_losses >= self.config.parking_on_consecutive_losses:
            return True

        # Parking sur drawdown
        if game_state.current_drawdown >= self.config.parking_on_drawdown_percent:
            return True

        # Déléguer à la stratégie de base si elle veut attendre
        if self.base_strategy and hasattr(self.base_strategy, "should_wait"):
            return self.base_strategy.should_wait(game_state)

        return False

    def can_toggle_bet_type(self) -> bool:
        """Vérifie si on peut encore toggle UNDER/OVER."""
        return self.toggles_count < self.config.max_toggles_before_bet

    def should_rotate_seed(self, game_state: GameState, current_nonce: int) -> bool:
        """Détermine si on doit faire une rotation de seed."""
        # Rotation préventive
        if (
            current_nonce - self.last_seed_rotation_nonce
            >= self.config.auto_seed_rotation_after
        ):
            return True

        # Rotation sur pertes importantes
        if game_state.consecutive_losses >= self.config.seed_rotation_on_losses:
            return True

        return False

    def calculate_next_bet(self, game_state: GameState) -> Decimal:
        """Calcule le montant du prochain pari."""
        if self.is_parking:
            return self.config.parking_bet_amount

        if self.base_strategy:
            return self.base_strategy.calculate_next_bet(game_state)

        return self.config.base_bet

    def select_target(self, game_state: GameState) -> float:
        """Sélectionne le target."""
        if self.is_parking:
            return self.config.parking_target

        if self.base_strategy:
            return self.base_strategy.select_target(game_state)

        return self.config.default_target

    def select_bet_type(self, game_state: GameState) -> BetType:
        """Sélectionne le type de pari."""
        if self.is_parking:
            return self.config.parking_bet_type

        if self.base_strategy:
            return self.base_strategy.select_bet_type(game_state)

        return self.config.default_bet_type

    def decide_bet(self, game_state: GameState) -> BetDecision:
        """Décide de l'action à prendre (pari ou action alternative)."""
        # Récupérer le nonce actuel (à implémenter dans l'intégration)
        current_nonce = game_state.metadata.get("current_nonce", 0)

        # Vérifier si on doit entrer en mode parking
        if self.should_park(game_state):
            self.is_parking = True

            # Option 1: Rotation de seed
            if self.should_rotate_seed(game_state, current_nonce):
                self.last_seed_rotation_nonce = current_nonce
                self.toggles_count = 0  # Reset toggles
                game_state.seed_rotations_count += 1
                return BetDecision(
                    amount=Decimal("0"),
                    multiplier=2.0,
                    skip=True,
                    action="change_seed",
                    reason="Strategic seed rotation",
                )

            # Option 2: Toggle bet type
            if self.can_toggle_bet_type():
                self.toggles_count += 1
                game_state.bet_type_toggles += 1
                # Toggle le type actuel
                new_type = (
                    BetType.OVER
                    if game_state.current_bet_type == BetType.UNDER
                    else BetType.UNDER
                )
                return BetDecision(
                    amount=Decimal("0"),
                    multiplier=2.0,
                    bet_type=new_type,
                    skip=True,
                    action="toggle_bet_type",
                    reason=(
                        f"Toggle {self.toggles_count}/"
                        f"{self.config.max_toggles_before_bet}"
                    ),
                )

            # Option 3: Pari parking forcé
            self.parking_bets_count += 1
            game_state.parking_bets_count += 1
            return BetDecision(
                amount=self.config.parking_bet_amount,
                multiplier=self._target_to_multiplier(
                    self.config.parking_target, self.config.parking_bet_type
                ),
                target=self.config.parking_target,
                bet_type=self.config.parking_bet_type,
                confidence=0.1,  # Faible confiance car forcé
                action="forced_parking_bet",
                reason=f"Forced parking bet #{self.parking_bets_count}",
            )
        else:
            # Mode normal
            self.is_parking = False
            self.toggles_count = 0  # Reset pour la prochaine fois

            # Déléguer à la stratégie de base
            if self.base_strategy:
                decision = self.base_strategy.decide_bet(game_state)
                return decision
            else:
                # Décision par défaut
                return super().decide_bet(game_state)

    def _update_strategy_state(self, result: BetResult) -> None:
        """Met à jour l'état après un résultat."""
        # Tracker les pertes de parking
        if (
            hasattr(result, "metadata")
            and result.metadata.get("action") == "forced_parking_bet"
        ):
            if not result.won:
                # Ajouter aux pertes de parking dans GameState
                # (nécessite accès au GameState, à implémenter dans l'intégration)
                pass

        # Mettre à jour la stratégie de base si elle existe
        if self.base_strategy:
            self.base_strategy.update_after_result(result)

    def reset_state(self) -> None:
        """Réinitialise l'état de la stratégie."""
        self.toggles_count = 0
        self.parking_bets_count = 0
        self.is_parking = False

        if self.base_strategy:
            self.base_strategy.reset_state()

    def _target_to_multiplier(self, target: float, bet_type: BetType) -> float:
        """Convertit un target en multiplicateur."""
        if bet_type == BetType.UNDER:
            win_chance = target * 0.99  # House edge 1%
        else:
            win_chance = (100 - target) * 0.99

        return 100.0 / win_chance if win_chance > 0 else 99.0

    def get_name(self) -> str:
        """Retourne le nom de la stratégie."""
        base_name = self.base_strategy.get_name() if self.base_strategy else "None"
        return f"Parking({base_name})"

    def get_status(self) -> dict[str, Any]:
        """Retourne le statut actuel de la stratégie."""
        status = {
            "is_parking": self.is_parking,
            "toggles_count": self.toggles_count,
            "parking_bets_count": self.parking_bets_count,
            "can_toggle": self.can_toggle_bet_type(),
        }

        if self.base_strategy:
            status["base_strategy_status"] = self.base_strategy.get_status()

        return status
