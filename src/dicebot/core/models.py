from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from .constants import MIN_BET_LTC


class BetType(Enum):
    """Type de pari : UNDER (roll < target) ou OVER (roll > target)."""

    UNDER = "under"
    OVER = "over"


@dataclass
class GameConfig:
    house_edge: float = 0.01
    min_bet_ltc: Decimal = Decimal("0.00015")
    max_bet_ltc: Decimal = Decimal("1000")
    bet_delay_min: float = 1.5
    bet_delay_max: float = 3.0


@dataclass
class VaultConfig:
    total_capital: Decimal
    vault_ratio: float = 0.85
    session_bankroll_ratio: float = 0.15

    @property
    def vault_amount(self) -> Decimal:
        return (self.total_capital * Decimal(str(self.vault_ratio))).quantize(Decimal("0.00"))

    @property
    def bankroll_amount(self) -> Decimal:
        return self.total_capital - self.vault_amount


@dataclass
class BetResult:
    roll: float
    won: bool
    threshold: float
    amount: Decimal
    payout: Decimal
    timestamp: datetime = None

    # Informations OVER/UNDER (compatibles Bitsler)
    bet_type: BetType = BetType.UNDER
    target: float = 50.0

    # Informations Provably Fair (compatibles Bitsler)
    server_seed_hash: str | None = None
    client_seed: str | None = None
    nonce: int | None = None

    # Pour vérification ultérieure
    multiplier: float | None = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

    @property
    def profit(self) -> Decimal:
        """Profit de ce pari (payout - amount)."""
        return self.payout - self.amount

    def to_verification_dict(self) -> dict[str, Any]:
        """Convertit en dict pour vérification provably fair."""
        return {
            "server_seed_hash": self.server_seed_hash,
            "client_seed": self.client_seed,
            "nonce": self.nonce,
            "multiplier": self.multiplier,
            "bet_type": self.bet_type.value,
            "target": self.target,
            "roll": self.roll,
            "won": self.won,
            "threshold": self.threshold,
            "amount": float(self.amount),
            "payout": float(self.payout),
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


@dataclass
class GameState:
    balance: Decimal
    bets_count: int = 0
    wins_count: int = 0
    losses_count: int = 0
    total_wagered: Decimal = Decimal("0")
    total_profit: Decimal = Decimal("0")
    max_balance: Decimal = None
    min_balance: Decimal = None
    consecutive_wins: int = 0
    consecutive_losses: int = 0

    # Métriques avancées
    max_consecutive_wins: int = 0
    max_consecutive_losses: int = 0
    current_drawdown: Decimal = Decimal("0")
    max_drawdown: Decimal = Decimal("0")
    drawdown_start: datetime | None = None

    # Historique des derniers paris (réduit pour optimiser la mémoire)
    bet_history: list[BetResult] = field(default_factory=list)
    history_limit: int = 20

    # État de la session
    session_start_balance: Decimal | None = None
    session_start_time: datetime | None = None

    # État OVER/UNDER
    current_bet_type: BetType = BetType.UNDER
    current_target: float = 50.0

    # Métriques Parking & Provably Fair
    parking_bets_count: int = 0
    parking_losses: Decimal = Decimal("0")
    seed_rotations_count: int = 0
    bet_type_toggles: int = 0

    # Metadata flexible pour stocker des informations supplémentaires
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.max_balance is None:
            self.max_balance = self.balance
        if self.min_balance is None:
            self.min_balance = self.balance
        if self.session_start_balance is None:
            self.session_start_balance = self.balance
        if self.session_start_time is None:
            self.session_start_time = datetime.now()

    def update(self, result: BetResult):
        self.bets_count += 1
        self.total_wagered += result.amount

        # Ajouter à l'historique
        self.bet_history.append(result)
        if len(self.bet_history) > self.history_limit:
            self.bet_history.pop(0)

        if result.won:
            self.wins_count += 1
            self.consecutive_wins += 1
            self.consecutive_losses = 0
            self.balance += result.payout - result.amount
            self.total_profit += result.payout - result.amount
            # Mettre à jour le max de gains consécutifs
            self.max_consecutive_wins = max(self.max_consecutive_wins, self.consecutive_wins)
        else:
            self.losses_count += 1
            self.consecutive_losses += 1
            self.consecutive_wins = 0
            self.balance -= result.amount
            self.total_profit -= result.amount
            # Mettre à jour le max de pertes consécutives
            self.max_consecutive_losses = max(self.max_consecutive_losses, self.consecutive_losses)

        # Mettre à jour les balances min/max
        self.max_balance = max(self.max_balance, self.balance)
        self.min_balance = min(self.min_balance, self.balance)

        # Calculer le drawdown
        if self.balance < self.max_balance:
            self.current_drawdown = (self.max_balance - self.balance) / self.max_balance
            self.max_drawdown = max(self.max_drawdown, self.current_drawdown)
            if self.drawdown_start is None:
                self.drawdown_start = datetime.now()
        else:
            self.current_drawdown = Decimal("0")
            self.drawdown_start = None

    @property
    def win_rate(self) -> float:
        if self.bets_count == 0:
            return 0.0
        return self.wins_count / self.bets_count

    @property
    def roi(self) -> float:
        if self.total_wagered == 0:
            return 0.0
        return float(self.total_profit / self.total_wagered)

    @property
    def sharpe_ratio(self) -> float:
        """Calcule le Sharpe ratio simplifié (rendement/risque)."""
        if len(self.bet_history) < 2:
            return 0.0

        returns = []
        for i in range(1, len(self.bet_history)):
            bet = self.bet_history[i]
            profit = (bet.payout - bet.amount) if bet.won else -bet.amount
            returns.append(float(profit / bet.amount))

        if not returns:
            return 0.0

        avg_return = sum(returns) / len(returns)
        if len(returns) < 2:
            return avg_return

        variance = sum((r - avg_return) ** 2 for r in returns) / (len(returns) - 1)
        std_dev = variance**0.5

        if std_dev == 0:
            return 0.0

        return avg_return / std_dev

    @property
    def session_duration(self) -> float:
        """Durée de la session en secondes."""
        if self.session_start_time is None:
            return 0.0
        return (datetime.now() - self.session_start_time).total_seconds()

    @property
    def bets_per_minute(self) -> float:
        """Nombre de paris par minute."""
        duration_minutes = self.session_duration / 60
        if duration_minutes == 0:
            return 0.0
        return self.bets_count / duration_minutes

    @property
    def session_roi(self) -> float:
        """ROI de la session en cours."""
        if self.session_start_balance == 0:
            return 0.0
        profit = self.balance - self.session_start_balance
        return float(profit / self.session_start_balance)


@dataclass
class BetDecision:
    amount: Decimal
    multiplier: float
    bet_type: BetType = BetType.UNDER
    target: float = 50.0
    skip: bool = False
    reason: str | None = None
    confidence: float = 1.0  # Niveau de confiance dans la décision (0-1)
    metadata: dict[str, Any] = field(default_factory=dict)  # Données additionnelles
    action: str | None = None  # "change_seed", "toggle_bet_type", "forced_parking_bet"


@dataclass
class SessionState:
    """État complet d'une session de jeu."""

    game_state: GameState
    session_id: str
    bot_id: str = "manual"  # Pour phase 1, sera UUID en phase 2
    strategy_name: str = "unknown"

    # Métadonnées de session
    started_at: datetime = field(default_factory=datetime.now)
    ended_at: datetime | None = None
    stop_reason: str | None = None

    # Configuration de session
    stop_loss: Decimal | None = None
    take_profit: Decimal | None = None
    max_bets: int | None = None

    # Métriques de session
    peak_balance: Decimal = field(init=False)
    lowest_balance: Decimal = field(init=False)
    total_session_time: float = 0.0

    def __post_init__(self):
        self.peak_balance = self.game_state.balance
        self.lowest_balance = self.game_state.balance

    def update(self, result: BetResult):
        """Met à jour l'état avec un nouveau résultat."""
        self.game_state.update(result)
        self.peak_balance = max(self.peak_balance, self.game_state.balance)
        self.lowest_balance = min(self.lowest_balance, self.game_state.balance)

    def should_stop(self) -> tuple[bool, str | None]:
        """Vérifie si la session doit s'arrêter."""
        # Stop loss
        if self.stop_loss and self.game_state.session_roi <= -abs(float(self.stop_loss)):
            return True, "stop_loss"

        # Take profit
        if self.take_profit and self.game_state.session_roi >= float(self.take_profit):
            return True, "take_profit"

        # Max bets
        if self.max_bets and self.game_state.bets_count >= self.max_bets:
            return True, "max_bets"

        # Balance insuffisante
        if self.game_state.balance < MIN_BET_LTC:
            return True, "insufficient_balance"

        return False, None

    def end_session(self, reason: str):
        """Termine la session."""
        self.ended_at = datetime.now()
        self.stop_reason = reason
        self.total_session_time = (self.ended_at - self.started_at).total_seconds()
