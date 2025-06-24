# 🎲 Système Provably Fair - Compatible Bitsler

DiceBot intègre un système **Provably Fair** 100% compatible avec Bitsler.com, garantissant la transparence et la vérifiabilité de tous les résultats de dés.

## 🎯 Vue d'ensemble

Le système Provably Fair permet de :
- ✅ **Vérifier** que tous les résultats sont équitables et non manipulés
- ✅ **Reproduire** exactement les résultats avec les mêmes seeds
- ✅ **Auditer** l'historique complet des paris
- ✅ **Garantir** la compatibilité 100% avec l'algorithme Bitsler

## 🔧 Composants du Système

### 1. Seeds (Graines)

| Composant | Description | Visibilité | Exemple |
|-----------|-------------|------------|---------|
| **Server Seed** | Graine générée par le serveur | Hash visible uniquement | `e6bbf5eda32e178e78a2c8e73b4b8bea...` |
| **Client Seed** | Graine choisie par le joueur | Entièrement visible | `my_custom_seed_123` |
| **Nonce** | Compteur incrémenté à chaque pari | Visible | `0, 1, 2, 3...` |

### 2. Algorithme Bitsler

```python
# 1. Créer le message
message = f"{client_seed},{nonce}"

# 2. Calculer HMAC-SHA512  
seed_hash = hmac.new(server_seed.encode(), message.encode(), hashlib.sha512).hexdigest()

# 3. Extraire un nombre valide (≤ 999999)
offset = 0
while offset + 5 <= len(seed_hash):
    hex_chunk = seed_hash[offset:offset + 5]
    number = int(hex_chunk, 16)
    if number <= 999999:
        break
    offset += 5

# 4. Calculer le résultat de dés
dice_result = (number % 10000) / 100  # Résultat entre 0.00 et 99.99
```

## 🚀 Utilisation Pratique

### Configuration Simple

```python
from dicebot.core import DiceGame

# Mode Provably Fair (par défaut)
game = DiceGame()

# Avec seeds personnalisés
game = DiceGame(
    server_seed="mon_server_seed",  # Optionnel pour tests
    client_seed="mon_client_seed"   # Optionnel
)
```

### Gestion des Seeds

```python
# Obtenir les informations de seed actuelles
seed_info = game.get_current_seed_info()
print(f"Server Seed Hash: {seed_info['server_seed_hash']}")
print(f"Client Seed: {seed_info['client_seed']}")
print(f"Nonce: {seed_info['nonce']}")

# Changer le client seed
game.set_client_seed("nouveau_seed_perso")

# Rotation des seeds (révèle l'ancien server seed)
old_seeds = game.rotate_seeds()
print(f"Ancien Server Seed révélé: {old_seeds['server_seed']}")
```

### Paris avec Informations Provably Fair

```python
from decimal import Decimal

# Effectuer un pari
result = game.roll(Decimal("1.0"), 2.0)

print(f"Résultat: {result.roll}")
print(f"Gagné: {result.won}")
print(f"Server Seed Hash: {result.server_seed_hash}")
print(f"Client Seed: {result.client_seed}")
print(f"Nonce: {result.nonce}")
```

### Vérification des Résultats

```python
# Après rotation des seeds, vérifier un ancien résultat
verification = game.verify_result(result)

if verification and verification["is_valid"]:
    print("✅ Résultat vérifié comme équitable!")
    print(f"Calculé: {verification['calculated_result']}")
    print(f"Attendu: {verification['expected_result']}")
else:
    print("❌ Résultat invalide!")
```

## 🔒 Contrainte de Nonce Séquentiel

### Exigence Critique de Bitsler

Sur Bitsler, **chaque nonce doit être utilisé séquentiellement** (0, 1, 2, 3...). Vous ne pouvez pas "sauter" un nonce - c'est une contrainte fondamentale du système Provably Fair.

### Conséquences pour les Stratégies

1. **Impossible de "pausser"** : Toute stratégie qui veut attendre doit faire un pari
2. **Paris forcés** : Si votre stratégie ne veut pas parier, vous devez quand même consommer le nonce
3. **Actions alternatives** : Pour éviter de parier sans stratégie

### Actions Sans Consommer de Nonce

| Action | Effet | Utilisation |
|--------|-------|-------------|
| **Toggle UNDER/OVER** | Change le type de pari | Peut être répété plusieurs fois |
| **Rotation de seed** | Reset le nonce à 0 | Révèle l'ancien server seed |

### ParkingStrategy - Solution Intelligente

La `ParkingStrategy` gère automatiquement cette contrainte :

```python
from dicebot.strategies.parking import ParkingConfig, ParkingStrategy

# Configuration du parking
parking_config = ParkingConfig(
    base_bet=Decimal("0.001"),
    parking_bet_amount=Decimal("0.00015"),  # Mise minimum
    parking_target=98.0,  # 99% de chance de gagner
    max_toggles_before_bet=3,  # Toggles avant pari forcé
    parking_on_consecutive_losses=5,  # Active parking après 5 pertes
)

# Wrapper une stratégie existante
base_strategy = StrategyFactory.create("martingale", strategy_config)
parking = ParkingStrategy(parking_config)
parking.set_base_strategy(base_strategy)
```

### Séquence de Parking Typique

1. **Détection** : La stratégie veut attendre (5+ pertes consécutives)
2. **Toggle 1** : Change UNDER → OVER (pas de nonce consommé)
3. **Toggle 2** : Change OVER → UNDER (pas de nonce consommé) 
4. **Toggle 3** : Change UNDER → OVER (pas de nonce consommé)
5. **Pari forcé** : Mise minimum à 98% de chance (consomme le nonce)

### Métriques de Parking

Le système trace le coût du parking :

```python
game_state.parking_bets_count    # Nombre de paris parking
game_state.parking_losses        # Pertes totales en parking
game_state.seed_rotations_count  # Rotations de seed effectuées
game_state.bet_type_toggles      # Toggles UNDER/OVER
```

### Configuration YAML

```yaml
parking:
  enabled: true
  max_toggles_before_bet: 3
  parking_bet_amount: 0.00015
  parking_target: 98.0
  parking_bet_type: "UNDER"
  auto_seed_rotation_after: 1000
  parking_on_consecutive_losses: 5
  parking_on_drawdown_percent: 0.1
```

## 🔍 Vérification Manuelle

### Utilisation du Vérificateur

```python
from dicebot.core.provably_fair import BitslerVerifier

# Vérifier un résultat spécifique
verification = BitslerVerifier.verify_dice_result(
    server_seed="e6bbf5eda32e178e78a2c8e73b4b8bea1c17e01ac5b8e5c0d42d2a29f4b76eb7",
    client_seed="test_client",
    nonce=0,
    expected_result=42.15
)

print(f"Valide: {verification['is_valid']}")
print(f"Message: {verification['message']}")
print(f"Hash: {verification['hmac_sha512'][:50]}...")
print(f"Nombre extrait: {verification['extracted_number']}")
```

### Vérification en Batch

```python
# Vérifier plusieurs résultats d'un coup
results = [
    {"server_seed": "seed1", "client_seed": "client", "nonce": 0, "result": 15.67},
    {"server_seed": "seed1", "client_seed": "client", "nonce": 1, "result": 78.42},
    # ... plus de résultats
]

batch_verification = BitslerVerifier.batch_verify(results)
print(f"Taux de succès: {batch_verification['success_rate']:.2%}")
```

## 📊 Compatibilité avec Bitsler

### Algorithme Identique

Notre implémentation utilise **exactement** le même algorithme que Bitsler :

1. ✅ **HMAC-SHA512** avec les mêmes paramètres
2. ✅ **Extraction par chunks de 5 hex** avec condition ≤ 999999
3. ✅ **Calcul du résultat** : `(number % 10000) / 100`
4. ✅ **Format des messages** : `"{client_seed},{nonce}"`

### Vérification Croisée

Vous pouvez vérifier nos résultats sur :
- **Vérificateur officiel Bitsler** : https://www.bitsler.com/en/provably-fair
- **Vérificateurs tiers** : DiceSites.com, etc.

## 🔐 Sécurité et Transparence

### Principes de Sécurité

1. **Server Seed caché** : Seul le hash est visible pendant le jeu
2. **Client Seed modifiable** : Le joueur contrôle cette partie
3. **Nonce incrémental** : Impossible de répéter un résultat
4. **Révélation post-rotation** : Server seed révélé après changement

### Garanties

- 🛡️ **Impossible de prédire** les résultats futurs
- 🔍 **Possible de vérifier** tous les résultats passés
- 🎯 **Impossible de manipuler** les résultats
- ✅ **100% transparent** et auditable

## 🧪 Mode Test vs Production

### Mode Legacy (Tests)

```python
# Pour les tests reproductibles
game = DiceGame(use_provably_fair=False, seed=12345)

# Résultats identiques à chaque exécution
result1 = game.roll(Decimal("1"), 2.0)
result2 = game.roll(Decimal("1"), 2.0)
# result1.roll != result2.roll mais reproductible entre runs
```

### Mode Provably Fair (Production)

```python
# Mode par défaut - cryptographiquement sécurisé
game = DiceGame()

# Chaque résultat est unique et vérifiable
result = game.roll(Decimal("1"), 2.0)
print(f"Hash: {result.server_seed_hash}")
print(f"Nonce: {result.nonce}")
```

## 📈 Intégration dans les Stratégies

### Accès aux Informations de Seed

```python
class MyStrategy(BaseStrategy):
    def calculate_next_bet(self, game_state: GameState) -> BetDecision:
        # Accéder aux informations de seed via game_state.bet_history
        if game_state.bet_history:
            last_bet = game_state.bet_history[-1]
            print(f"Dernier nonce: {last_bet.nonce}")
            print(f"Hash utilisé: {last_bet.server_seed_hash}")
        
        return BetDecision(amount=self.config.base_bet, multiplier=2.0)
```

### Rotation Automatique des Seeds

```python
# Rotation périodique pour plus de sécurité
class AutoRotateStrategy(BaseStrategy):
    def __init__(self, config, rotation_frequency=1000):
        super().__init__(config)
        self.rotation_frequency = rotation_frequency
        self.bets_since_rotation = 0
    
    def calculate_next_bet(self, game_state: GameState) -> BetDecision:
        self.bets_since_rotation += 1
        
        # Rotation automatique tous les N paris
        if self.bets_since_rotation >= self.rotation_frequency:
            # Note: Nécessiterait accès au DiceGame
            # game.rotate_seeds()
            self.bets_since_rotation = 0
        
        return BetDecision(amount=self.config.base_bet, multiplier=2.0)
```

## 🔗 Ressources Supplémentaires

### Documentation Bitsler

- [Provably Fair officiel](https://www.bitsler.com/en/provably-fair)
- [Guide Bitsler Help Center](https://help.bitsler.com/en/articles/6635997-all-about-bet-fairness-in-online-gambling)

### Vérificateurs Externes

- [DiceSites Bitsler Verifier](https://dicesites.com/bitsler/verifier)
- [Provably Fair explanation](https://dicesites.com/provably-fair)

### Code Source

- `src/dicebot/core/provably_fair.py` - Implémentation complète
- `src/dicebot/core/dice_game.py` - Intégration dans DiceGame
- `tests/core/test_provably_fair.py` - Tests de compatibilité

---

## ✅ Checklist de Vérification

Avant d'utiliser le système en production :

- [ ] Tester avec des seeds connus
- [ ] Vérifier la compatibilité avec le vérificateur Bitsler
- [ ] Confirmer que les hashs de server seed correspondent
- [ ] Valider la séquence de nonce (pas de saut)
- [ ] Effectuer une rotation de seeds et vérifier l'historique
- [ ] Tester ParkingStrategy avec vos stratégies
- [ ] Vérifier les métriques de parking

**🎲 Le système Provably Fair de DiceBot garantit une transparence totale et une compatibilité parfaite avec Bitsler, incluant le respect de la contrainte de nonce séquentiel !**
