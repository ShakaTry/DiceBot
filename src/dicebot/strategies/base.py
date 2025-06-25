from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from ..core.constants import MAX_BET_LTC, MIN_BET_LTC
from ..core.events import EventBus, StreakEvent
from ..core.models import BetDecision, BetResult, BetType, GameState


@dataclass
class StrategyConfig:
    """Configuration commune pour toutes les stratégies"""

    base_bet: Decimal
    min_bet: Decimal = MIN_BET_LTC
    max_bet: Decimal = MAX_BET_LTC
    multiplier: float = 2.0  # Pour stratégies qui multiplient
    max_losses: int = 10  # Protection contre les séries
    default_multiplier: float = 2.0  # Multiplicateur de jeu par défaut (legacy)

    # Paramètres OVER/UNDER
    default_bet_type: BetType = BetType.UNDER
    default_target: float = 50.0
    allow_bet_type_switching: bool = False  # Permet aux stratégies de changer OVER/UNDER
    allow_target_adjustment: bool = False  # Permet aux stratégies d'ajuster le target


class BaseStrategy(ABC):
    """Classe abstraite pour toutes les stratégies de paris"""

    def __init__(self, config: StrategyConfig, event_bus: EventBus | None = None):
        self.config = config
        self.current_bet = config.base_bet
        from ..core.events import event_bus as global_event_bus

        self.event_bus = event_bus or global_event_bus
        self.confidence = 1.0  # Niveau de confiance (0-1)
        self.metrics = StrategyMetrics()
        self._previous_state: GameState | None = None
        self.reset_state()

    @abstractmethod
    def calculate_next_bet(self, game_state: GameState) -> Decimal:
        """Calcule la prochaine mise basée sur l'état du jeu"""
        pass

    def select_bet_type(self, game_state: GameState) -> BetType:
        """Sélectionne le type de pari (UNDER/OVER). Peut être surchargée."""
        return self.config.default_bet_type

    def select_target(self, game_state: GameState) -> float:
        """Sélectionne le target pour le pari. Peut être surchargée."""
        if self.config.allow_target_adjustment:
            # Convertir le multiplicateur par défaut en target
            return self._multiplier_to_target(
                self.config.default_multiplier, self.select_bet_type(game_state)
            )
        return self.config.default_target

    def _multiplier_to_target(self, multiplier: float, bet_type: BetType) -> float:
        """Convertit un multiplicateur en target selon le type de pari."""
        # Win chance = 100 / multiplier
        # Avec house edge: raw_chance = win_chance / (1 - house_edge)
        house_edge = 0.01  # Valeur par défaut, pourrait être configurable
        win_chance = 100.0 / multiplier
        raw_chance = win_chance / (1 - house_edge)

        if bet_type == BetType.UNDER:
            target = raw_chance
        else:  # BetType.OVER
            target = 100.0 - raw_chance

        return max(0.01, min(99.99, target))

    def update_after_result(self, result: BetResult) -> None:
        """Met à jour l'état interne après un résultat"""
        # Appeler la méthode abstraite spécifique à chaque stratégie
        self._update_strategy_state(result)

        # Mettre à jour les métriques si on a un game_state
        if hasattr(self, "_last_game_state"):
            self.update_metrics(result, self._last_game_state)

    @abstractmethod
    def _update_strategy_state(self, result: BetResult) -> None:
        """Met à jour l'état spécifique à la stratégie.

        À implémenter dans les sous-classes.
        """
        pass

    @abstractmethod
    def reset_state(self) -> None:
        """Réinitialise l'état de la stratégie"""
        pass

    def decide_bet(self, game_state: GameState) -> BetDecision:
        """Interface principale pour décider du prochain pari"""
        # Détecter les séries et émettre des événements
        self._check_streaks(game_state)

        # Vérifier si on peut parier
        if game_state.balance < self.config.min_bet:
            return BetDecision(
                amount=Decimal("0"),
                multiplier=self.config.default_multiplier,
                bet_type=self.config.default_bet_type,
                target=self.config.default_target,
                skip=True,
                reason="Insufficient balance",
                confidence=0.0,
            )

        # Hook avant le calcul
        self.on_before_bet(game_state)

        # Calculer la mise
        next_bet = self.calculate_next_bet(game_state)

        # Appliquer les limites
        next_bet = self._apply_limits(next_bet, game_state.balance)

        # Si la mise est trop petite après les limites
        if next_bet < self.config.min_bet:
            return BetDecision(
                amount=Decimal("0"),
                multiplier=self.config.default_multiplier,
                bet_type=self.config.default_bet_type,
                target=self.config.default_target,
                skip=True,
                reason="Bet below minimum after limits",
                confidence=self.confidence,
            )

        # Calculer la confiance
        self._update_confidence(game_state)

        # Sélectionner le type de pari et le target
        bet_type = self.select_bet_type(game_state)
        target = self.select_target(game_state)

        # Calculer le multiplicateur équivalent pour compatibilité
        equivalent_multiplier = self._target_to_multiplier(target, bet_type)

        # Retourner la décision avec support OVER/UNDER
        decision = BetDecision(
            amount=next_bet,
            multiplier=equivalent_multiplier,  # Pour compatibilité legacy
            bet_type=bet_type,
            target=target,
            skip=False,
            confidence=self.confidence,
            metadata={
                "strategy": self.get_name(),
                "consecutive_losses": game_state.consecutive_losses,
                "consecutive_wins": game_state.consecutive_wins,
                "bet_type": bet_type.value,
                "target": target,
            },
        )

        # Hook après la décision
        self.on_after_decision(decision, game_state)

        # Sauvegarder l'état pour les métriques
        self._last_game_state = game_state
        self._previous_state = game_state
        return decision

    def _apply_limits(self, bet: Decimal, balance: Decimal) -> Decimal:
        """Applique les limites min/max et vérifie le bankroll"""
        # Limites absolues
        bet = max(self.config.min_bet, min(bet, self.config.max_bet))

        # Limite du bankroll
        bet = min(bet, balance)

        return bet

    def get_name(self) -> str:
        """Retourne le nom de la stratégie"""
        return self.__class__.__name__.replace("Strategy", "")

    def _target_to_multiplier(self, target: float, bet_type: BetType) -> float:
        """Convertit un target en multiplicateur équivalent."""
        house_edge = 0.01  # Valeur par défaut

        if bet_type == BetType.UNDER:
            raw_chance = target
        else:  # BetType.OVER
            raw_chance = 100.0 - target

        # Appliquer le house edge
        win_chance = raw_chance * (1 - house_edge)

        # Calculer le multiplicateur
        if win_chance <= 0:
            return 99.0  # Max multiplier

        multiplier = 100.0 / win_chance
        return max(1.01, min(99.0, multiplier))

    def get_genome(self) -> dict[str, Any]:
        """Retourne la configuration génétique de la stratégie.

        Pour évolution future.
        """
        return {
            "strategy_type": self.get_name(),
            "base_bet": str(self.config.base_bet),
            "min_bet": str(self.config.min_bet),
            "max_bet": str(self.config.max_bet),
            "multiplier": self.config.multiplier,
            "max_losses": self.config.max_losses,
            "default_multiplier": self.config.default_multiplier,
            "default_bet_type": self.config.default_bet_type.value,
            "default_target": self.config.default_target,
            "allow_bet_type_switching": self.config.allow_bet_type_switching,
            "allow_target_adjustment": self.config.allow_target_adjustment,
            "confidence": self.confidence,
            "fitness": self.calculate_fitness(),
            "generation": 0,  # Phase 1
            "mutations": [],  # Phase 2+
        }

    def calculate_fitness(self) -> float:
        """Calcule le score de fitness de la stratégie."""
        if self.metrics.total_bets == 0:
            return 0.0

        # Fitness basé sur plusieurs critères
        roi_score = max(0, min(1, (self.metrics.roi + 1) / 2))  # Normaliser ROI entre 0-1
        win_rate_score = self.metrics.win_rate
        survival_score = 1.0 if self.metrics.total_bets > 0 else 0.0

        # Pénaliser les drawdowns importants
        drawdown_penalty = 1.0 - min(1.0, abs(float(self.metrics.max_drawdown)) * 2)

        # Score composite
        fitness = (
            roi_score * 0.4 + win_rate_score * 0.2 + survival_score * 0.2 + drawdown_penalty * 0.2
        )

        return fitness

    def update_metrics(self, result: BetResult, game_state: GameState):
        """Met à jour les métriques de performance."""
        self.metrics.total_bets += 1
        self.metrics.total_wagered += result.amount

        if result.won:
            self.metrics.total_wins += 1
            profit = result.payout - result.amount
        else:
            self.metrics.total_losses += 1
            profit = -result.amount

        self.metrics.total_profit += profit
        self.metrics.max_bet_reached = max(self.metrics.max_bet_reached, result.amount)
        self.metrics.max_consecutive_losses = max(
            self.metrics.max_consecutive_losses, game_state.consecutive_losses
        )

        # Calculer le drawdown
        if game_state.current_drawdown > self.metrics.max_drawdown:
            self.metrics.max_drawdown = game_state.current_drawdown

    # Hooks pour l'extensibilité
    def on_before_bet(self, game_state: GameState) -> None:
        """Hook appelé avant de calculer le prochain pari."""
        _ = game_state  # Unused parameter

    def on_after_decision(self, decision: BetDecision, game_state: GameState) -> None:
        """Hook appelé après avoir pris une décision."""
        _ = decision, game_state  # Unused parameters

    def on_winning_streak(self, streak_length: int, game_state: GameState) -> None:
        """Hook appelé lors d'une série de gains."""
        _ = streak_length, game_state  # Unused parameters

    def on_losing_streak(self, streak_length: int, game_state: GameState) -> None:
        """Hook appelé lors d'une série de pertes."""
        _ = streak_length, game_state  # Unused parameters

    # Méthodes privées
    def _check_streaks(self, game_state: GameState) -> None:
        """Vérifie les séries et émet des événements."""
        if game_state.consecutive_wins >= 3:
            self.on_winning_streak(game_state.consecutive_wins, game_state)
            if game_state.consecutive_wins % 5 == 0:  # Tous les 5 gains
                self.event_bus.emit(StreakEvent("win", game_state.consecutive_wins, game_state))

        if game_state.consecutive_losses >= 3:
            self.on_losing_streak(game_state.consecutive_losses, game_state)
            if game_state.consecutive_losses % 5 == 0:  # Toutes les 5 pertes
                self.event_bus.emit(StreakEvent("loss", game_state.consecutive_losses, game_state))

    def _update_confidence(self, game_state: GameState) -> None:
        """Met à jour le niveau de confiance basé sur les performances récentes."""
        # Diminuer la confiance en cas de pertes consécutives
        if game_state.consecutive_losses > 0:
            self.confidence *= 0.95**game_state.consecutive_losses
        # Augmenter la confiance en cas de gains
        elif game_state.consecutive_wins > 0:
            self.confidence = min(1.0, self.confidence * 1.05)

        # Ajuster selon le drawdown
        if game_state.current_drawdown > Decimal("0.1"):  # Plus de 10% de drawdown
            self.confidence *= 0.9

        # S'assurer que la confiance reste dans les limites
        self.confidence = max(0.1, min(1.0, self.confidence))


@dataclass
class StrategyMetrics:
    """Métriques de performance d'une stratégie"""

    total_bets: int = 0
    total_wins: int = 0
    total_losses: int = 0
    max_bet_reached: Decimal = Decimal("0")
    max_consecutive_losses: int = 0
    total_wagered: Decimal = Decimal("0")
    total_profit: Decimal = Decimal("0")
    max_drawdown: Decimal = Decimal("0")
    total_confidence: float = 0.0

    # Métriques temporelles
    first_bet_time: datetime | None = None
    last_bet_time: datetime | None = None
    total_active_time: float = 0.0

    @property
    def win_rate(self) -> float:
        if self.total_bets == 0:
            return 0.0
        return self.total_wins / self.total_bets

    @property
    def roi(self) -> float:
        if self.total_wagered == 0:
            return 0.0
        return float(self.total_profit / self.total_wagered)

    @property
    def average_confidence(self) -> float:
        if self.total_bets == 0:
            return 0.0
        return self.total_confidence / self.total_bets

    @property
    def profit_factor(self) -> float:
        """Ratio des gains totaux sur les pertes totales."""
        if self.total_losses == 0:
            return float("inf") if self.total_wins > 0 else 0.0
        loss_ratio = Decimal(str(self.total_losses)) / Decimal(str(self.total_bets))
        total_win_amount = self.total_profit + self.total_wagered * loss_ratio
        total_loss_amount = self.total_wagered * loss_ratio
        return float(total_win_amount / total_loss_amount) if total_loss_amount > 0 else 0.0
