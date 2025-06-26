"""Système d'événements pour l'extensibilité du bot."""

from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import Any

from .models import BetDecision, BetResult, GameState


class EventType(Enum):
    """Types d'événements du système."""

    # Événements de jeu
    BET_PLACED = auto()
    BET_RESOLVED = auto()
    ROLL_PRE = auto()
    ROLL_POST = auto()

    # Événements de session
    SESSION_START = auto()
    SESSION_END = auto()
    SESSION_PAUSE = auto()
    SESSION_RESUME = auto()

    # Événements de stratégie
    STRATEGY_CHANGED = auto()
    STRATEGY_CONFIDENCE_UPDATE = auto()

    # Événements de séries
    WINNING_STREAK = auto()
    LOSING_STREAK = auto()
    BREAK_EVEN = auto()

    # Événements financiers
    BALANCE_UPDATE = auto()
    DRAWDOWN_ALERT = auto()
    PROFIT_TARGET_REACHED = auto()
    STOP_LOSS_TRIGGERED = auto()

    # Événements futurs (Phase 2+)
    BOT_MUTATION = auto()
    CULTURE_UPDATE = auto()
    BELIEF_CHANGE = auto()


@dataclass
class Event:
    """Événement du système."""

    type: EventType
    timestamp: datetime
    data: dict[str, Any]
    source: str | None = None

    def __post_init__(self) -> None:
        # timestamp is required in dataclass, this check is no longer needed
        pass


@dataclass
class BetPlacedEvent(Event):
    """Événement quand un pari est placé."""

    def __init__(self, decision: BetDecision, game_state: GameState, strategy_name: str) -> None:
        super().__init__(
            type=EventType.BET_PLACED,
            timestamp=datetime.now(),
            data={
                "decision": decision,
                "game_state": game_state,
                "strategy": strategy_name,
            },
            source=strategy_name,
        )


@dataclass
class BetResolvedEvent(Event):
    """Événement quand un pari est résolu."""

    def __init__(self, result: BetResult, game_state: GameState, strategy_name: str) -> None:
        super().__init__(
            type=EventType.BET_RESOLVED,
            timestamp=datetime.now(),
            data={
                "result": result,
                "game_state": game_state,
                "strategy": strategy_name,
            },
            source=strategy_name,
        )


@dataclass
class StreakEvent(Event):
    """Événement de série (gains/pertes)."""

    def __init__(self, streak_type: str, length: int, game_state: GameState) -> None:
        event_type = EventType.WINNING_STREAK if streak_type == "win" else EventType.LOSING_STREAK
        super().__init__(
            type=event_type,
            timestamp=datetime.now(),
            data={
                "streak_type": streak_type,
                "length": length,
                "game_state": game_state,
            },
        )


class EventListener(ABC):
    """Interface pour les écouteurs d'événements."""

    @abstractmethod
    def on_event(self, event: Event) -> None:
        """Traite un événement."""
        pass

    def can_handle(self, event_type: EventType) -> bool:
        """Indique si ce listener peut traiter ce type d'événement."""
        return True


class EventBus:
    """Bus d'événements pour la communication entre composants."""

    def __init__(self) -> None:
        self._listeners: dict[EventType, list[EventListener]] = defaultdict(list)
        self._callbacks: dict[EventType, list[Callable[[Event], None]]] = defaultdict(list)
        self._history: list[Event] = []
        self._history_limit = 10000

    def subscribe(self, event_type: EventType, listener: EventListener) -> None:
        """Abonne un listener à un type d'événement."""
        if listener not in self._listeners[event_type]:
            self._listeners[event_type].append(listener)

    def subscribe_callback(self, event_type: EventType, callback: Callable[[Event], None]) -> None:
        """Abonne une fonction callback à un type d'événement."""
        if callback not in self._callbacks[event_type]:
            self._callbacks[event_type].append(callback)

    def unsubscribe(self, event_type: EventType, listener: EventListener) -> None:
        """Désabonne un listener."""
        if listener in self._listeners[event_type]:
            self._listeners[event_type].remove(listener)

    def emit(self, event: Event) -> None:
        """Émet un événement à tous les listeners concernés."""
        # Ajouter à l'historique
        self._history.append(event)
        if len(self._history) > self._history_limit:
            self._history.pop(0)

        # Notifier les listeners
        for listener in self._listeners.get(event.type, []):
            if listener.can_handle(event.type):
                listener.on_event(event)

        # Notifier les callbacks
        for callback in self._callbacks.get(event.type, []):
            callback(event)

    def get_history(self, event_type: EventType | None = None, limit: int = 100) -> list[Event]:
        """Récupère l'historique des événements."""
        history = (
            self._history
            if event_type is None
            else [e for e in self._history if e.type == event_type]
        )
        return history[-limit:]

    def clear_history(self) -> None:
        """Efface l'historique des événements."""
        self._history.clear()


# Instance globale du bus d'événements (peut être remplacée par injection de dépendance)
event_bus = EventBus()
