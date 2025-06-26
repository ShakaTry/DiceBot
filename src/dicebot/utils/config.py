"""
Configuration management for DiceBot.
"""

from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml

from ..core.models import GameConfig, VaultConfig


class DiceBotConfig:
    """Main configuration class for DiceBot."""

    DEFAULT_CONFIG = {
        "simulation": {
            "default_sessions": 100,
            "parallel_workers": 4,
            "memory_limit_mb": 512,
            "auto_parallel_threshold": 50,
            "progress_bar": True,
        },
        "strategies": {
            "presets": {
                "conservative": {
                    "base_bet": "0.0005",
                    "max_losses": 5,
                    "multiplier": 2.0,
                },
                "moderate": {"base_bet": "0.001", "max_losses": 8, "multiplier": 2.0},
                "aggressive": {
                    "base_bet": "0.002",
                    "max_losses": 12,
                    "multiplier": 2.0,
                },
                "experimental": {
                    "base_bet": "0.003",
                    "max_losses": 15,
                    "multiplier": 2.5,
                },
            },
            "risk_levels": {
                "low": {"max_losses": 5, "max_capital_ratio": 0.05},
                "medium": {"max_losses": 10, "max_capital_ratio": 0.10},
                "high": {"max_losses": 15, "max_capital_ratio": 0.20},
                "extreme": {"max_losses": 20, "max_capital_ratio": 0.35},
            },
        },
        "game": {
            "house_edge": 0.01,
            "min_bet_ltc": "0.00015",
            "max_bet_ltc": "1000",
            "bet_delay_min": 1.5,
            "bet_delay_max": 3.0,
        },
        "vault": {"vault_ratio": 0.85, "session_bankroll_ratio": 0.15},
        "output": {
            "format": "json",  # json, csv, parquet
            "compression": None,  # gzip, bz2, None
            "auto_cleanup_days": 30,
            "include_session_details": True,
        },
        "cli": {
            "default_output_dir": "results",
            "color_output": True,
            "show_warnings": True,
        },
    }

    def __init__(self, config_file: Path | str | None = None):
        """Initialize configuration.

        Args:
            config_file: Path to config file. If None, uses default locations.
        """
        self.config = self.DEFAULT_CONFIG.copy()
        self.config_file = None

        if config_file:
            self.load_from_file(Path(config_file))
        else:
            # Try to load from default locations
            self._load_from_default_locations()

    def _load_from_default_locations(self):
        """Try to load config from default locations."""
        default_locations = [
            Path.cwd() / "dicebot.yaml",
            Path.cwd() / "dicebot.yml",
            Path.cwd() / ".dicebot.yaml",
            Path.home() / ".dicebot" / "config.yaml",
            Path.home() / ".config" / "dicebot" / "config.yaml",
        ]

        for location in default_locations:
            if location.exists():
                try:
                    self.load_from_file(location)
                    break
                except (OSError, yaml.YAMLError, ValueError):
                    continue  # Try next location

    def load_from_file(self, config_file: Path):
        """Load configuration from YAML file.

        Args:
            config_file: Path to YAML configuration file
        """
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_file}")

        try:
            with open(config_file, encoding="utf-8") as f:
                user_config = yaml.safe_load(f)

            if user_config:
                self._merge_config(self.config, user_config)
                self.config_file = config_file

        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in config file {config_file}: {e}") from e

    def _merge_config(self, base: dict, override: dict):
        """Recursively merge configuration dictionaries."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value

    def save_to_file(self, config_file: Path):
        """Save current configuration to YAML file.

        Args:
            config_file: Path where to save the configuration
        """
        config_file.parent.mkdir(parents=True, exist_ok=True)

        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(self.config, f, default_flow_style=False, indent=2)

        self.config_file = config_file

    # Convenience property accessors
    @property
    def simulation(self) -> dict[str, Any]:
        return self.config["simulation"]

    @property
    def strategies(self) -> dict[str, Any]:
        return self.config["strategies"]

    @property
    def game(self) -> dict[str, Any]:
        return self.config["game"]

    @property
    def vault(self) -> dict[str, Any]:
        return self.config["vault"]

    @property
    def output(self) -> dict[str, Any]:
        return self.config["output"]

    @property
    def cli(self) -> dict[str, Any]:
        return self.config["cli"]

    # Factory methods for model creation
    def create_game_config(self) -> GameConfig:
        """Create GameConfig from configuration."""
        game_cfg = self.game
        return GameConfig(
            house_edge=game_cfg["house_edge"],
            min_bet_ltc=Decimal(str(game_cfg["min_bet_ltc"])),
            max_bet_ltc=Decimal(str(game_cfg["max_bet_ltc"])),
            bet_delay_min=game_cfg["bet_delay_min"],
            bet_delay_max=game_cfg["bet_delay_max"],
        )

    def create_vault_config(self, total_capital: Decimal) -> VaultConfig:
        """Create VaultConfig from configuration.

        Args:
            total_capital: Total capital amount

        Returns:
            VaultConfig instance
        """
        vault_cfg = self.vault
        return VaultConfig(
            total_capital=total_capital,
            vault_ratio=vault_cfg["vault_ratio"],
            session_bankroll_ratio=vault_cfg["session_bankroll_ratio"],
        )

    def get_strategy_preset(self, preset_name: str) -> dict[str, Any]:
        """Get strategy preset configuration.

        Args:
            preset_name: Name of the preset

        Returns:
            Strategy configuration dictionary

        Raises:
            KeyError: If preset doesn't exist
        """
        presets = self.strategies["presets"]
        if preset_name not in presets:
            available = ", ".join(presets.keys())
            raise KeyError(f"Preset '{preset_name}' not found. Available: {available}")

        return presets[preset_name].copy()

    def get_risk_level_config(self, risk_level: str) -> dict[str, Any]:
        """Get risk level configuration.

        Args:
            risk_level: Risk level name (low, medium, high, extreme)

        Returns:
            Risk configuration dictionary
        """
        risk_levels = self.strategies["risk_levels"]
        if risk_level not in risk_levels:
            available = ", ".join(risk_levels.keys())
            raise KeyError(f"Risk level '{risk_level}' not found. Available: {available}")

        return risk_levels[risk_level].copy()

    def assess_strategy_risk(self, strategy_config: dict[str, Any], capital: Decimal) -> str:
        """Assess the risk level of a strategy configuration.

        Args:
            strategy_config: Strategy configuration
            capital: Total capital

        Returns:
            Risk level string (low, medium, high, extreme)
        """
        max_losses = strategy_config.get("max_losses", 10)
        base_bet = Decimal(str(strategy_config.get("base_bet", "0.001")))

        # Calculate capital ratio
        capital_ratio = float(base_bet / capital)

        # Check against risk levels
        risk_levels = self.strategies["risk_levels"]

        for level in ["low", "medium", "high", "extreme"]:
            level_config = risk_levels[level]
            if (
                max_losses <= level_config["max_losses"]
                and capital_ratio <= level_config["max_capital_ratio"]
            ):
                return level

        return "extreme"

    def suggest_improvements(self, strategy_config: dict[str, Any], capital: Decimal) -> list[str]:
        """Suggest improvements for a strategy configuration.

        Args:
            strategy_config: Strategy configuration
            capital: Total capital

        Returns:
            List of suggestion strings
        """
        suggestions = []

        risk_level = self.assess_strategy_risk(strategy_config, capital)

        if risk_level in ["high", "extreme"]:
            max_losses = strategy_config.get("max_losses", 10)
            base_bet = Decimal(str(strategy_config.get("base_bet", "0.001")))

            # Suggest reducing max_losses
            if max_losses > 10:
                suggestions.append(f"Consider reducing max_losses from {max_losses} to 8-10")

            # Suggest reducing base_bet
            capital_ratio = float(base_bet / capital)
            if capital_ratio > 0.001:
                safer_bet = capital * Decimal("0.001")
                suggestions.append(f"Consider reducing base_bet to {safer_bet:.6f} LTC")

            # Suggest preset
            if risk_level == "extreme":
                suggestions.append("Consider using the 'conservative' preset")
            else:
                suggestions.append("Consider using the 'moderate' preset")

        return suggestions


# Global configuration instance
_global_config = None


def get_config() -> DiceBotConfig:
    """Get global configuration instance."""
    global _global_config
    if _global_config is None:
        _global_config = DiceBotConfig()
    return _global_config


def set_config(config: DiceBotConfig):
    """Set global configuration instance."""
    global _global_config
    _global_config = config
