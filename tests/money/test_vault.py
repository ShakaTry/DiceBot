from decimal import Decimal

import pytest

from dicebot.core import VaultConfig
from dicebot.money import Vault


class TestVault:
    def test_initialization(self):
        config = VaultConfig(total_capital=Decimal("100"))
        vault = Vault(config)

        assert vault.state.vault_balance == Decimal("85")  # 85%
        assert vault.state.bankroll_balance == Decimal("15")  # 15%
        assert vault.state.total_balance == Decimal("100")

    def test_deposit(self):
        config = VaultConfig(total_capital=Decimal("100"))
        vault = Vault(config)

        vault.deposit(Decimal("50"))

        assert vault.state.vault_balance == Decimal("127.5")  # 85 + 42.5
        assert vault.state.bankroll_balance == Decimal("22.5")  # 15 + 7.5
        assert vault.state.total_deposited == Decimal("150")

    def test_withdraw_from_vault(self):
        config = VaultConfig(total_capital=Decimal("100"))
        vault = Vault(config)

        withdrawn = vault.withdraw_from_vault(Decimal("10"))

        assert withdrawn == Decimal("10")
        assert vault.state.vault_balance == Decimal("75")
        assert vault.state.total_withdrawn == Decimal("10")

    def test_withdraw_insufficient_funds(self):
        config = VaultConfig(total_capital=Decimal("100"))
        vault = Vault(config)

        with pytest.raises(ValueError, match="Insufficient vault balance"):
            vault.withdraw_from_vault(Decimal("100"))

    def test_transfer_between_vault_and_bankroll(self):
        config = VaultConfig(total_capital=Decimal("100"))
        vault = Vault(config)

        # Transfer to bankroll
        vault.transfer_to_bankroll(Decimal("10"))
        assert vault.state.vault_balance == Decimal("75")
        assert vault.state.bankroll_balance == Decimal("25")

        # Transfer back to vault
        vault.transfer_to_vault(Decimal("5"))
        assert vault.state.vault_balance == Decimal("80")
        assert vault.state.bankroll_balance == Decimal("20")

    def test_allocate_session_bankroll(self):
        config = VaultConfig(total_capital=Decimal("100"))
        vault = Vault(config)

        # Default 15% of bankroll (from session_bankroll_ratio)
        session_amount = vault.allocate_session_bankroll()
        assert session_amount == Decimal("2.25")  # 15% of 15

        # Custom ratio
        session_amount = vault.allocate_session_bankroll(0.5)
        assert session_amount == Decimal("7.5")  # 50% of 15

    def test_return_session_profit(self):
        config = VaultConfig(total_capital=Decimal("100"))
        vault = Vault(config)

        # Test profit scenario
        initial = Decimal("10")
        final = Decimal("20")
        vault.return_session_profit(initial, final)

        # Profit of 10, split 85/15
        assert vault.state.vault_balance == Decimal("93.5")  # 85 + 8.5
        assert vault.state.bankroll_balance == Decimal("16.5")  # 15 + 1.5

        # Test loss scenario
        initial = Decimal("10")
        final = Decimal("5")
        vault.return_session_profit(initial, final)

        # Loss of 5, taken from bankroll
        assert vault.state.vault_balance == Decimal("93.5")
        assert vault.state.bankroll_balance == Decimal("11.5")  # 16.5 - 5

    def test_rebalance(self):
        config = VaultConfig(total_capital=Decimal("100"))
        vault = Vault(config)

        # Manually unbalance
        vault.transfer_to_bankroll(Decimal("20"))
        assert vault.state.vault_balance == Decimal("65")
        assert vault.state.bankroll_balance == Decimal("35")

        # Rebalance
        vault.rebalance()
        assert vault.state.vault_balance == Decimal("85")
        assert vault.state.bankroll_balance == Decimal("15")

    def test_get_stats(self):
        config = VaultConfig(total_capital=Decimal("100"))
        vault = Vault(config)

        stats = vault.get_stats()

        assert stats["vault_balance"] == 85.0
        assert stats["bankroll_balance"] == 15.0
        assert stats["total_balance"] == 100.0
        assert stats["vault_ratio"] == 0.85
        assert stats["net_profit"] == 0.0
