from decimal import Decimal
from typing import Any

from ..core.constants import MAX_BET_LTC, MIN_BET_LTC
from .adaptive import AdaptiveConfig, AdaptiveStrategy
from .base import BaseStrategy, StrategyConfig
from .composite import CombinationMode, CompositeConfig, CompositeStrategy
from .dalembert import DAlembert
from .fibonacci import FibonacciStrategy
from .flat import FlatBetting
from .martingale import MartingaleStrategy
from .paroli import ParoliStrategy


class StrategyFactory:
    """Factory pour créer des instances de stratégies"""

    _strategies: dict[str, type[BaseStrategy]] = {
        "martingale": MartingaleStrategy,
        "fibonacci": FibonacciStrategy,
        "dalembert": DAlembert,
        "flat": FlatBetting,
        "paroli": ParoliStrategy,
        "composite": CompositeStrategy,
        "adaptive": AdaptiveStrategy,
    }

    @classmethod
    def create(cls, name: str, config: StrategyConfig, **kwargs) -> BaseStrategy:
        """
        Crée une instance de stratégie.

        Args:
            name: Nom de la stratégie
            config: Configuration de la stratégie
            **kwargs: Arguments supplémentaires spécifiques à certaines stratégies

        Returns:
            Instance de la stratégie

        Raises:
            ValueError: Si la stratégie n'existe pas ou si la configuration est invalide
        """
        if name not in cls._strategies:
            available = ", ".join(cls._strategies.keys())
            raise ValueError(
                f"Unknown strategy: '{name}'. Available strategies: {available}"
            )

        # Valider la configuration
        cls._validate_config(config, name)

        strategy_class = cls._strategies[name]

        # Certaines stratégies ont des paramètres spécifiques
        if name == "paroli" and "target_wins" in kwargs:
            target_wins = kwargs["target_wins"]
            if not isinstance(target_wins, int) or target_wins < 1:
                raise ValueError("target_wins must be a positive integer")
            return strategy_class(config, target_wins=target_wins)

        # CompositeStrategy nécessite une liste de stratégies
        if name == "composite" and "strategies" in kwargs:
            strategies = kwargs["strategies"]
            if not isinstance(strategies, list) or not strategies:
                raise ValueError(
                    "composite strategy requires a non-empty list of strategies"
                )
            return strategy_class(config, strategies)

        # AdaptiveStrategy a déjà sa configuration spécialisée
        if name == "adaptive":
            if not isinstance(config, AdaptiveConfig):
                raise ValueError("adaptive strategy requires AdaptiveConfig")

        return strategy_class(config)

    @classmethod
    def create_from_dict(cls, config_dict: dict[str, Any]) -> BaseStrategy:
        """
        Crée une stratégie à partir d'un dictionnaire de configuration.

        Args:
            config_dict: Dictionnaire contenant:
                - strategy: nom de la stratégie
                - base_bet: mise de base
                - min_bet: mise minimum (optionnel)
                - max_bet: mise maximum (optionnel)
                - multiplier: multiplicateur (optionnel)
                - max_losses: pertes max (optionnel)
                - Autres paramètres spécifiques

        Returns:
            Instance de la stratégie
        """
        # Extraire le nom de la stratégie
        strategy_name = config_dict.pop("strategy")

        # Extraire les paramètres spécifiques à certaines stratégies
        special_params = {}
        if strategy_name == "paroli" and "target_wins" in config_dict:
            special_params["target_wins"] = config_dict.pop("target_wins")

        # Convertir les valeurs monétaires en Decimal si nécessaire
        for field in ["base_bet", "min_bet", "max_bet"]:
            if field in config_dict and not isinstance(config_dict[field], Decimal):
                config_dict[field] = Decimal(str(config_dict[field]))

        # Valider les types des autres champs
        if "multiplier" in config_dict:
            config_dict["multiplier"] = float(config_dict["multiplier"])

        if "max_losses" in config_dict:
            config_dict["max_losses"] = int(config_dict["max_losses"])

        if "default_multiplier" in config_dict:
            config_dict["default_multiplier"] = float(config_dict["default_multiplier"])

        # Créer la configuration spécifique à chaque stratégie
        if strategy_name == "adaptive":
            # Traiter les règles pour AdaptiveStrategy
            if "rules" in config_dict:
                from .adaptive import StrategyRule, SwitchCondition

                rules = []
                for rule_dict in config_dict["rules"]:
                    if isinstance(rule_dict, dict):
                        condition = SwitchCondition[rule_dict["condition"]]
                        rule = StrategyRule(
                            condition=condition,
                            threshold=rule_dict["threshold"],
                            target_strategy=rule_dict["target_strategy"],
                            target_config=rule_dict.get("target_config", {}),
                            cooldown_bets=rule_dict.get("cooldown_bets", 10),
                        )
                        rules.append(rule)
                config_dict["rules"] = rules

            strategy_config = AdaptiveConfig(**config_dict)
        else:
            strategy_config = StrategyConfig(**config_dict)

        # Créer la stratégie (la validation sera faite dans create())
        return cls.create(strategy_name, strategy_config, **special_params)

    @classmethod
    def list_available(cls) -> list[str]:
        """Retourne la liste des stratégies disponibles"""
        return list(cls._strategies.keys())

    @classmethod
    def register_strategy(cls, name: str, strategy_class: type[BaseStrategy]) -> None:
        """
        Enregistre une nouvelle stratégie dans la factory.

        Args:
            name: Nom de la stratégie
            strategy_class: Classe de la stratégie
        """
        cls._strategies[name] = strategy_class

    @classmethod
    def _validate_config(cls, config: StrategyConfig, strategy_name: str) -> None:
        """
        Valide la configuration d'une stratégie.

        Args:
            config: Configuration à valider
            strategy_name: Nom de la stratégie

        Raises:
            ValueError: Si la configuration est invalide
        """
        # Validations communes
        if config.base_bet <= 0:
            raise ValueError("base_bet must be positive")

        if config.base_bet < MIN_BET_LTC:
            raise ValueError(f"base_bet must be at least {MIN_BET_LTC} LTC")

        if config.base_bet > MAX_BET_LTC:
            raise ValueError(f"base_bet must not exceed {MAX_BET_LTC} LTC")

        if config.min_bet < MIN_BET_LTC:
            raise ValueError(f"min_bet must be at least {MIN_BET_LTC} LTC")

        if config.max_bet > MAX_BET_LTC:
            raise ValueError(f"max_bet must not exceed {MAX_BET_LTC} LTC")

        if config.min_bet > config.max_bet:
            raise ValueError("min_bet cannot be greater than max_bet")

        if config.base_bet < config.min_bet or config.base_bet > config.max_bet:
            raise ValueError("base_bet must be between min_bet and max_bet")

        if config.multiplier < 1.01 or config.multiplier > 99:
            raise ValueError("multiplier must be between 1.01 and 99")

        if config.max_losses < 1 or config.max_losses > 1000:
            raise ValueError("max_losses must be between 1 and 1000")

        # Validations spécifiques par stratégie
        if strategy_name == "martingale":
            # Vérifier que le bankroll peut supporter les pertes max avec le multiplier
            max_possible_bet = config.base_bet * (
                Decimal(str(config.multiplier)) ** config.max_losses
            )
            if max_possible_bet > config.max_bet:
                import math

                ratio = float(config.max_bet) / float(config.base_bet)
                suggested_max_losses = int(math.log(ratio, config.multiplier))
                raise ValueError(
                    f"With base_bet={config.base_bet} and multiplier={config.multiplier}, "
                    f"max_losses={config.max_losses} would require bets up to {max_possible_bet}. "
                    f"Consider reducing max_losses to {suggested_max_losses} or less."
                )

        elif strategy_name == "fibonacci":
            # Vérifier que la séquence Fibonacci ne dépasse pas les limites
            fib_sequence = [1, 1]
            for _ in range(config.max_losses - 2):
                fib_sequence.append(fib_sequence[-1] + fib_sequence[-2])

            max_fib_bet = config.base_bet * Decimal(str(fib_sequence[-1]))
            if max_fib_bet > config.max_bet:
                raise ValueError(
                    f"Fibonacci sequence at position {config.max_losses} would "
                    f"require bets up to {max_fib_bet}. Reduce max_losses."
                )

        elif strategy_name == "dalembert":
            # D'Alembert a une progression linéaire
            max_dalembert_bet = config.base_bet * Decimal(str(config.max_losses))
            if max_dalembert_bet > config.max_bet:
                suggested_max_losses = int(config.max_bet / config.base_bet)
                raise ValueError(
                    f"D'Alembert with {config.max_losses} units would require "
                    f"bets up to {max_dalembert_bet}. Maximum units: {suggested_max_losses}"
                )

    @classmethod
    def create_composite(
        cls,
        strategies: list[tuple[str, dict[str, Any]]],
        mode: str = "weighted",
        base_config: dict[str, Any] | None = None,
    ) -> CompositeStrategy:
        """
        Crée une stratégie composite qui combine plusieurs stratégies.

        Args:
            strategies: Liste de tuples (nom_stratégie, config_dict)
            mode: Mode de combinaison (average, weighted, consensus, aggressive, conservative, rotate)
            base_config: Configuration de base pour la stratégie composite

        Returns:
            Instance de CompositeStrategy

        Example:
            composite = StrategyFactory.create_composite([
                ("martingale", {"base_bet": 0.001, "max_losses": 5}),
                ("fibonacci", {"base_bet": 0.001, "max_losses": 8}),
                ("dalembert", {"base_bet": 0.001, "max_losses": 10})
            ], mode="weighted")
        """
        if not strategies:
            raise ValueError("At least one strategy is required for composite")

        # Créer les sous-stratégies
        sub_strategies = []
        for strategy_name, strategy_config in strategies:
            sub_strategy = cls.create_from_dict(
                {"strategy": strategy_name, **strategy_config}
            )
            sub_strategies.append(sub_strategy)

        # Configurer la stratégie composite
        composite_config = base_config or {}

        # Utiliser la base_bet de la première stratégie si non spécifiée
        if "base_bet" not in composite_config:
            composite_config["base_bet"] = sub_strategies[0].config.base_bet

        # Convertir le mode string en enum
        try:
            mode_enum = CombinationMode[mode.upper()]
        except KeyError:
            available_modes = ", ".join([m.name.lower() for m in CombinationMode])
            raise ValueError(
                f"Invalid mode '{mode}'. Available modes: {available_modes}"
            )

        composite_config["mode"] = mode_enum

        # Créer la configuration composite
        config = CompositeConfig(**composite_config)

        return CompositeStrategy(config, sub_strategies)
