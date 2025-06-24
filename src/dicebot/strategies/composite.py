"""Stratégie composite qui peut combiner plusieurs stratégies."""

from collections import Counter
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum, auto

from ..core.models import BetDecision, BetResult, BetType, GameState
from .base import BaseStrategy, StrategyConfig


class CombinationMode(Enum):
    """Mode de combinaison des stratégies."""

    AVERAGE = auto()  # Moyenne des décisions
    WEIGHTED = auto()  # Moyenne pondérée par confiance
    CONSENSUS = auto()  # Majorité des stratégies doivent être d'accord
    AGGRESSIVE = auto()  # Prend la mise la plus élevée
    CONSERVATIVE = auto()  # Prend la mise la plus faible
    ROTATE = auto()  # Alterne entre les stratégies


@dataclass
class CompositeConfig(StrategyConfig):
    """Configuration pour la stratégie composite."""

    mode: CombinationMode = CombinationMode.WEIGHTED
    consensus_threshold: float = 0.5  # Pour le mode CONSENSUS
    rotation_interval: int = 10  # Nombre de paris avant rotation


class CompositeStrategy(BaseStrategy):
    """
    Stratégie qui combine plusieurs stratégies selon différents modes.

    Permet de bénéficier des avantages de plusieurs approches et de
    mitiger les risques en diversifiant les décisions.
    """

    def __init__(self, config: CompositeConfig, strategies: list[BaseStrategy]):
        """
        Args:
            config: Configuration de la stratégie composite
            strategies: Liste des stratégies à combiner
        """
        if not strategies:
            raise ValueError("At least one strategy is required")

        # Initialiser les attributs AVANT d'appeler super().__init__()
        self.strategies = strategies
        self.mode = config.mode
        self.consensus_threshold = config.consensus_threshold
        self.rotation_interval = config.rotation_interval
        self.current_strategy_index = 0
        self.bets_since_rotation = 0

        super().__init__(config)

        # Initialiser toutes les sous-stratégies
        for strategy in self.strategies:
            strategy.reset_state()

    def calculate_next_bet(self, game_state: GameState) -> Decimal:
        """Calcule la prochaine mise en combinant les stratégies."""
        # Utiliser la méthode helper pour obtenir les décisions combinées
        combined_decision = self._get_combined_decision(game_state)
        return (
            combined_decision.amount
            if combined_decision and not combined_decision.skip
            else self.config.base_bet
        )

    def select_bet_type(self, game_state: GameState) -> BetType:
        """Sélectionne le type de pari en combinant les stratégies."""
        combined_decision = self._get_combined_decision(game_state)
        return (
            combined_decision.bet_type
            if combined_decision
            else self.config.default_bet_type
        )

    def select_target(self, game_state: GameState) -> float:
        """Sélectionne le target en combinant les stratégies."""
        combined_decision = self._get_combined_decision(game_state)
        return (
            combined_decision.target
            if combined_decision
            else self.config.default_target
        )

    def _get_combined_decision(self, game_state: GameState) -> BetDecision | None:
        """Obtient la décision combinée de toutes les stratégies."""
        decisions = []
        total_confidence = 0.0

        # Collecter les décisions de toutes les stratégies
        for strategy in self.strategies:
            decision = strategy.decide_bet(game_state)
            if not decision.skip:
                decisions.append((strategy, decision))
                total_confidence += decision.confidence

        if not decisions:
            return None

        # Appliquer le mode de combinaison
        if self.mode == CombinationMode.AVERAGE:
            return self._average_mode_full(decisions)

        elif self.mode == CombinationMode.WEIGHTED:
            return self._weighted_mode_full(decisions, total_confidence)

        elif self.mode == CombinationMode.CONSENSUS:
            return self._consensus_mode_full(decisions, game_state)

        elif self.mode == CombinationMode.AGGRESSIVE:
            return self._aggressive_mode_full(decisions)

        elif self.mode == CombinationMode.CONSERVATIVE:
            return self._conservative_mode_full(decisions)

        elif self.mode == CombinationMode.ROTATE:
            return self._rotate_mode_full(game_state)

        return BetDecision(
            amount=self.config.base_bet,
            multiplier=self.config.default_multiplier,
            bet_type=self.config.default_bet_type,
            target=self.config.default_target,
        )

    def _update_strategy_state(self, result: BetResult) -> None:
        """Met à jour l'état de toutes les stratégies."""
        for strategy in self.strategies:
            strategy.update_after_result(result)

        # Incrémenter le compteur pour la rotation
        if self.mode == CombinationMode.ROTATE:
            self.bets_since_rotation += 1
            if self.bets_since_rotation >= self.rotation_interval:
                self.current_strategy_index = (self.current_strategy_index + 1) % len(
                    self.strategies
                )
                self.bets_since_rotation = 0

    def reset_state(self) -> None:
        """Réinitialise l'état de toutes les stratégies."""
        for strategy in self.strategies:
            strategy.reset_state()

        self.current_strategy_index = 0
        self.bets_since_rotation = 0
        self.confidence = 1.0

    # Modes de combinaison complets (OVER/UNDER)
    def _average_mode_full(
        self, decisions: list[tuple[BaseStrategy, BetDecision]]
    ) -> BetDecision:
        """Calcule la moyenne des décisions."""
        # Moyenne des montants
        avg_amount = sum(decision.amount for _, decision in decisions) / len(decisions)

        # Moyenne des targets
        avg_target = sum(decision.target for _, decision in decisions) / len(decisions)

        # Type de pari majoritaire
        bet_types = [decision.bet_type for _, decision in decisions]
        majority_type = Counter(bet_types).most_common(1)[0][0]

        # Confiance moyenne
        avg_confidence = sum(decision.confidence for _, decision in decisions) / len(
            decisions
        )

        return BetDecision(
            amount=avg_amount,
            multiplier=self._target_to_multiplier(avg_target, majority_type),
            bet_type=majority_type,
            target=avg_target,
            confidence=avg_confidence,
        )

    # Méthodes legacy pour compatibilité
    def _average_mode(
        self, decisions: list[tuple[BaseStrategy, BetDecision]]
    ) -> Decimal:
        """Calcule la moyenne simple des mises (legacy)."""
        total = sum(decision.amount for _, decision in decisions)
        return total / len(decisions)

    def _weighted_mode_full(
        self, decisions: list[tuple[BaseStrategy, BetDecision]], total_confidence: float
    ) -> BetDecision:
        """Calcule la moyenne pondérée par la confiance."""
        if total_confidence == 0:
            return self._average_mode_full(decisions)

        # Montant pondéré
        weighted_amount = sum(
            decision.amount * Decimal(str(decision.confidence))
            for _, decision in decisions
        ) / Decimal(str(total_confidence))

        # Target pondéré
        weighted_target = (
            sum(decision.target * decision.confidence for _, decision in decisions)
            / total_confidence
        )

        # Type majoritaire pondéré par confiance
        type_weights = {}
        for _, decision in decisions:
            if decision.bet_type not in type_weights:
                type_weights[decision.bet_type] = 0
            type_weights[decision.bet_type] += decision.confidence

        best_type = max(type_weights.items(), key=lambda x: x[1])[0]

        return BetDecision(
            amount=weighted_amount,
            multiplier=self._target_to_multiplier(weighted_target, best_type),
            bet_type=best_type,
            target=weighted_target,
            confidence=total_confidence / len(decisions),
        )

    def _weighted_mode(
        self, decisions: list[tuple[BaseStrategy, BetDecision]], total_confidence: float
    ) -> Decimal:
        """Calcule la moyenne pondérée par la confiance (legacy)."""
        if total_confidence == 0:
            return self._average_mode(decisions)

        weighted_sum = sum(
            decision.amount * Decimal(str(decision.confidence))
            for _, decision in decisions
        )
        return weighted_sum / Decimal(str(total_confidence))

    def _consensus_mode_full(
        self, decisions: list[tuple[BaseStrategy, BetDecision]], game_state: GameState
    ) -> BetDecision:
        """Requiert qu'une majorité de stratégies soient d'accord (version complète)."""
        if not decisions:
            return BetDecision(
                amount=Decimal("0"), skip=True, reason="No valid decisions"
            )

        # Analyser les types de pari
        bet_types = [d.bet_type for _, d in decisions]
        type_consensus = Counter(bet_types).most_common(1)[0]

        if type_consensus[1] / len(decisions) < self.consensus_threshold:
            # Pas de consensus sur le type, utiliser base bet
            return BetDecision(
                amount=self.config.base_bet,
                multiplier=self.config.default_multiplier,
                bet_type=self.config.default_bet_type,
                target=self.config.default_target,
                reason="No bet type consensus",
            )

        # Filtrer les décisions du type consensuel
        consensus_decisions = [
            (s, d) for s, d in decisions if d.bet_type == type_consensus[0]
        ]

        # Analyser les montants (logique existante)
        groups = {}
        for strategy, decision in consensus_decisions:
            found_group = False
            for key in groups:
                if abs(float(decision.amount - key) / float(key)) < 0.1:
                    groups[key].append((strategy, decision))
                    found_group = True
                    break

            if not found_group:
                groups[decision.amount] = [(strategy, decision)]

        # Trouver le groupe avec le plus de consensus
        largest_group = max(groups.values(), key=len)

        # Vérifier si on a assez de consensus
        consensus_ratio = len(largest_group) / len(self.strategies)
        if consensus_ratio >= self.consensus_threshold:
            # Calculer la moyenne du groupe consensuel
            avg_amount = sum(d.amount for _, d in largest_group) / len(largest_group)
            avg_target = sum(d.target for _, d in largest_group) / len(largest_group)
            avg_confidence = sum(d.confidence for _, d in largest_group) / len(
                largest_group
            )

            return BetDecision(
                amount=avg_amount,
                multiplier=self._target_to_multiplier(avg_target, type_consensus[0]),
                bet_type=type_consensus[0],
                target=avg_target,
                confidence=avg_confidence,
            )

        # Pas assez de consensus, mise minimale
        return BetDecision(
            amount=self.config.base_bet,
            multiplier=self.config.default_multiplier,
            bet_type=self.config.default_bet_type,
            target=self.config.default_target,
            reason="Insufficient consensus",
        )

    def _consensus_mode(
        self, decisions: list[tuple[BaseStrategy, BetDecision]], game_state: GameState
    ) -> Decimal:
        """Requiert qu'une majorité de stratégies soient d'accord."""
        if not decisions:
            return Decimal("0")

        # Grouper les décisions similaires (±10% de différence)
        groups = {}
        for strategy, decision in decisions:
            found_group = False
            for key in groups:
                if abs(float(decision.amount - key) / float(key)) < 0.1:
                    groups[key].append((strategy, decision))
                    found_group = True
                    break

            if not found_group:
                groups[decision.amount] = [(strategy, decision)]

        # Trouver le groupe avec le plus de consensus
        largest_group = max(groups.values(), key=len)

        # Vérifier si on a assez de consensus
        consensus_ratio = len(largest_group) / len(self.strategies)
        if consensus_ratio >= self.consensus_threshold:
            # Retourner la moyenne du groupe consensuel
            return sum(d.amount for _, d in largest_group) / len(largest_group)

        # Pas assez de consensus, mise minimale
        return self.config.base_bet

    def _aggressive_mode_full(
        self, decisions: list[tuple[BaseStrategy, BetDecision]]
    ) -> BetDecision:
        """Prend la décision la plus agressive."""
        # Trouver la décision avec le montant le plus élevé
        _, max_decision = max(decisions, key=lambda x: x[1].amount)
        return max_decision

    def _aggressive_mode(
        self, decisions: list[tuple[BaseStrategy, BetDecision]]
    ) -> Decimal:
        """Prend la mise la plus élevée (legacy)."""
        return max(decision.amount for _, decision in decisions)

    def _conservative_mode_full(
        self, decisions: list[tuple[BaseStrategy, BetDecision]]
    ) -> BetDecision:
        """Prend la décision la plus conservative."""
        # Trouver la décision avec le montant le plus faible
        _, min_decision = min(decisions, key=lambda x: x[1].amount)
        return min_decision

    def _conservative_mode(
        self, decisions: list[tuple[BaseStrategy, BetDecision]]
    ) -> Decimal:
        """Prend la mise la plus faible (legacy)."""
        return min(decision.amount for _, decision in decisions)

    def _rotate_mode_full(self, game_state: GameState) -> BetDecision:
        """Utilise une stratégie différente à tour de rôle."""
        current_strategy = self.strategies[self.current_strategy_index]
        decision = current_strategy.decide_bet(game_state)

        if decision.skip:
            return BetDecision(
                amount=self.config.base_bet,
                multiplier=self.config.default_multiplier,
                bet_type=self.config.default_bet_type,
                target=self.config.default_target,
            )

        return decision

    def _rotate_mode(self, game_state: GameState) -> Decimal:
        """Utilise une stratégie différente à tour de rôle (legacy)."""
        current_strategy = self.strategies[self.current_strategy_index]
        decision = current_strategy.decide_bet(game_state)
        return decision.amount if not decision.skip else self.config.base_bet

    def get_name(self) -> str:
        """Retourne le nom de la stratégie composite."""
        strategy_names = [s.get_name() for s in self.strategies]
        return f"Composite({self.mode.name})[{','.join(strategy_names)}]"

    def _target_to_multiplier(self, target: float, bet_type: BetType) -> float:
        """Convertit un target en multiplicateur équivalent."""
        house_edge = 0.01

        if bet_type == BetType.UNDER:
            raw_chance = target
        else:  # BetType.OVER
            raw_chance = 100.0 - target

        win_chance = raw_chance * (1 - house_edge)

        if win_chance <= 0:
            return 99.0  # Max multiplier

        multiplier = 100.0 / win_chance
        return max(1.01, min(99.0, multiplier))

    def on_winning_streak(self, streak_length: int, game_state: GameState) -> None:
        """Propage l'événement à toutes les stratégies."""
        for strategy in self.strategies:
            strategy.on_winning_streak(streak_length, game_state)

    def on_losing_streak(self, streak_length: int, game_state: GameState) -> None:
        """Propage l'événement à toutes les stratégies."""
        for strategy in self.strategies:
            strategy.on_losing_streak(streak_length, game_state)
