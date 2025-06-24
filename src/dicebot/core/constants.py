from decimal import Decimal

# Bitsler specific constants
PLATFORM = "Bitsler"
CRYPTOCURRENCY = "LTC"
HOUSE_EDGE = 0.01  # 1%
MIN_BET_LTC = Decimal("0.00015")
MAX_BET_LTC = Decimal("1000")
MIN_MULTIPLIER = 1.01
MAX_MULTIPLIER = 99.00
BET_DELAY_MIN = 1.5  # seconds
BET_DELAY_MAX = 3.0  # seconds

# Vault/Bankroll management
DEFAULT_VAULT_RATIO = 0.85  # 85% in vault
DEFAULT_BANKROLL_RATIO = 0.15  # 15% for betting
DEFAULT_SESSION_BANKROLL_RATIO = 0.15  # 15% of bankroll per session

# Session limits
DEFAULT_STOP_LOSS = -0.50  # -50% of session bankroll
DEFAULT_TAKE_PROFIT = 1.00  # +100% of session bankroll
DEFAULT_MAX_BETS_PER_SESSION = 1000

# Strategy defaults
DEFAULT_BASE_BET_RATIO = 0.01  # 1% of session bankroll
