from dataclasses import dataclass
from decimal import Decimal

from ..core.models import VaultConfig


@dataclass
class VaultState:
    vault_balance: Decimal
    bankroll_balance: Decimal
    total_deposited: Decimal = Decimal("0")
    total_withdrawn: Decimal = Decimal("0")

    @property
    def total_balance(self) -> Decimal:
        return self.vault_balance + self.bankroll_balance

    @property
    def vault_ratio(self) -> float:
        if self.total_balance == 0:
            return 0.0
        return float(self.vault_balance / self.total_balance)

    @property
    def bankroll_ratio(self) -> float:
        if self.total_balance == 0:
            return 0.0
        return float(self.bankroll_balance / self.total_balance)


class Vault:
    def __init__(self, config: VaultConfig):
        self.config = config
        self.state = VaultState(
            vault_balance=config.vault_amount,
            bankroll_balance=config.bankroll_amount,
            total_deposited=config.total_capital,
        )

    def deposit(self, amount: Decimal) -> None:
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")

        vault_portion = amount * Decimal(str(self.config.vault_ratio))
        bankroll_portion = amount - vault_portion

        self.state.vault_balance += vault_portion
        self.state.bankroll_balance += bankroll_portion
        self.state.total_deposited += amount

    def withdraw_from_vault(self, amount: Decimal) -> Decimal:
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")

        if amount > self.state.vault_balance:
            raise ValueError(f"Insufficient vault balance: {self.state.vault_balance}")

        self.state.vault_balance -= amount
        self.state.total_withdrawn += amount
        return amount

    def transfer_to_bankroll(self, amount: Decimal) -> None:
        if amount <= 0:
            raise ValueError("Transfer amount must be positive")

        if amount > self.state.vault_balance:
            raise ValueError(f"Insufficient vault balance: {self.state.vault_balance}")

        self.state.vault_balance -= amount
        self.state.bankroll_balance += amount

    def transfer_to_vault(self, amount: Decimal) -> None:
        if amount <= 0:
            raise ValueError("Transfer amount must be positive")

        if amount > self.state.bankroll_balance:
            raise ValueError(
                f"Insufficient bankroll balance: {self.state.bankroll_balance}"
            )

        self.state.bankroll_balance -= amount
        self.state.vault_balance += amount

    def allocate_session_bankroll(self, ratio: float | None = None) -> Decimal:
        ratio = ratio or self.config.session_bankroll_ratio

        if ratio <= 0 or ratio > 1:
            raise ValueError("Session bankroll ratio must be between 0 and 1")

        session_amount = self.state.bankroll_balance * Decimal(str(ratio))

        if session_amount > self.state.bankroll_balance:
            session_amount = self.state.bankroll_balance

        return session_amount

    def return_session_profit(
        self, initial_amount: Decimal, final_amount: Decimal
    ) -> None:
        profit = final_amount - initial_amount

        if profit > 0:
            # Positive profit: split according to vault ratio
            vault_portion = profit * Decimal(str(self.config.vault_ratio))
            bankroll_portion = profit - vault_portion

            self.state.vault_balance += vault_portion
            self.state.bankroll_balance += bankroll_portion
        else:
            # Loss: deduct from bankroll
            loss = abs(profit)
            if loss > self.state.bankroll_balance:
                # Bankroll depleted, take from vault
                remaining_loss = loss - self.state.bankroll_balance
                self.state.bankroll_balance = Decimal("0")
                self.state.vault_balance -= remaining_loss
            else:
                self.state.bankroll_balance -= loss

    def rebalance(self) -> None:
        total = self.state.total_balance
        if total <= 0:
            return

        target_vault = total * Decimal(str(self.config.vault_ratio))
        # target_bankroll = total - target_vault  # Not used, calculated implicitly

        vault_diff = target_vault - self.state.vault_balance

        if vault_diff > 0:
            # Need to transfer to vault
            self.transfer_to_vault(vault_diff)
        elif vault_diff < 0:
            # Need to transfer to bankroll
            self.transfer_to_bankroll(abs(vault_diff))

    def can_start_session(self) -> bool:
        """Check if vault has enough funds to start a session."""
        return self.allocate_session_bankroll() > Decimal("0")

    def get_stats(self) -> dict:
        return {
            "vault_balance": float(self.state.vault_balance),
            "bankroll_balance": float(self.state.bankroll_balance),
            "total_balance": float(self.state.total_balance),
            "vault_ratio": self.state.vault_ratio,
            "bankroll_ratio": self.state.bankroll_ratio,
            "total_deposited": float(self.state.total_deposited),
            "total_withdrawn": float(self.state.total_withdrawn),
            "net_profit": float(
                self.state.total_balance
                - self.state.total_deposited
                + self.state.total_withdrawn
            ),
        }
