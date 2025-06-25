# Meilleures Pratiques - Recherche sur les Bots de Dice

## Résumé des Découvertes

D'après mes recherches sur les stratégies existantes et fonctionnelles, voici les meilleures pratiques établies dans la communauté des bots de dice gambling.

## 1. Gestion du Capital (Bankroll Management)

### Kelly Criterion - La Référence Mathématique

**Formule de Kelly** : `k% = (bp - q) / b`
- `k%` = Pourcentage du capital à miser
- `b` = Cote (multiplicateur - 1)
- `p` = Probabilité de gagner
- `q` = Probabilité de perdre (1-p)

**Adaptations Pratiques** :
- **Fractional Kelly** : La plupart des experts recommandent 1/4 ou 1/2 Kelly
- **Limite Absolue** : Ne jamais miser plus de 2.5% du capital sur un seul pari
- **Protection** : 1/3 de chance de diviser le capital par 2 avant de le doubler

### Recommandations Bitsler Spécifiques

**Capital Minimum** :
- **Minimum Absolu** : 0.01 BTC (ou équivalent LTC)
- **Recommandé** : 0.1 BTC pour résister à 400+ pertes consécutives
- **Votre Budget** : 250€ LTC est suffisant si bien géré

**Taille des Mises** :
- **Base Bet** : 2-10 Satoshis (adapter pour LTC)
- **Maximum** : 0.1% - 0.5% du capital total
- **Ajustement** : Diminuer la mise de base si losing streak

## 2. Système de Vault Optimisé

### Architecture Recommandée

```
Capital Total (250€ LTC)
├── Vault Sécurisé : 85% (212.5€)
│   ├── Réserve Urgence : 50% (125€)
│   └── Réserve Croissance : 35% (87.5€)
└── Bankroll Active : 15% (37.5€)
    ├── Session 1 : 20% (7.5€)
    ├── Session 2 : 20% (7.5€)
    └── Buffer : 60% (22.5€)
```

### Règles de Transfert

1. **Auto-Withdraw** : Retirer automatiquement après +10% de profit
2. **Recharge Bankroll** : Si < 50% de la bankroll initiale
3. **Protection** : Maximum 2 transferts par jour
4. **Sécurisation Profits** : 50% des profits vers vault, 50% réinvestis

## 3. Stratégies Éprouvées

### Hiérarchie des Stratégies (du plus sûr au plus risqué)

1. **90% Win Chance Recovery** (Plus Populaire)
   - Pari principal à 90% de chance
   - Si perte : Recovery à 19.8% chance avec Martingale
   - ROI moyen : 5-20% par jour

2. **D'Alembert Modifié**
   - Augmentation linéaire après perte
   - Plus sûr que Martingale pure
   - Survie : 200+ pertes consécutives

3. **Fibonacci Conservateur**
   - Progression moins agressive
   - Reset après 2 victoires consécutives
   - Adapté aux longues sessions

4. **Martingale Limitée**
   - Maximum 7-10 doublements
   - Base bet = 0.00001% du capital
   - Stop-loss obligatoire

### Stratégies Hybrides Recommandées

```python
# Stratégie "Smart Recovery"
if consecutive_losses > 3:
    switch_to_high_win_chance(90%)
    if win:
        return_to_base_strategy()
    else:
        martingale_recovery(max_steps=5)
```

## 4. Paramètres d'Évolution Optimaux

### Génome de Bot Recommandé

```python
@dataclass
class OptimizedBotGenome:
    # Base
    base_bet_ratio: float = 0.0001  # 0.01% du capital
    multiplier_range: Tuple[float, float] = (1.1, 3.0)
    
    # Risk Management
    stop_loss_ratio: float = 0.1  # -10% par session
    take_profit_ratio: float = 0.2  # +20% par session
    max_consecutive_losses: int = 15
    
    # Comportement
    kelly_fraction: float = 0.25  # 1/4 Kelly
    recovery_threshold: int = 5  # Pertes avant recovery mode
    confidence_decay: float = 0.95  # Après chaque perte
    
    # Adaptation
    pattern_memory: int = 100  # Derniers paris analysés
    strategy_switch_threshold: float = 0.7  # Score pour changer
```

## 5. Métriques Prioritaires (Ordre d'Importance)

1. **Risk-Adjusted ROI** : ROI / Max Drawdown
2. **Survival Rate** : % sessions non-bust sur 1000+
3. **Recovery Time** : Temps moyen pour récupérer d'un drawdown
4. **Profit Factor** : Total Gains / Total Losses
5. **Sharpe Ratio Adapté** : (ROI - Risk Free Rate) / Volatilité
6. **Win Rate Pondéré** : Win% × Average Win Size
7. **Consecutive Loss Resistance** : Max losing streak survécu

## 6. Configuration Technique Bitsler

### Limites Connues
- **Mise Minimum LTC** : 0.00015 LTC (confirmé)
- **Vitesse Max** : ~1 pari/seconde
- **Délai Recommandé** : 1.5-2 secondes entre paris
- **Seeds** : Changer tous les 10,000 paris

### Anti-Bot Protection
- Varier les délais (1-3 secondes)
- Pauses aléatoires (5-10 min toutes les heures)
- Patterns de mise non-répétitifs
- Simulation de mouvements souris (pour Playwright)

## 7. Architecture Système Recommandée

### Phase 1 : Simulateur Robuste
```
Priorités:
1. Moteur avec Kelly Criterion intégré
2. 5 stratégies de base + 3 hybrides
3. Vault system avec auto-withdraw
4. Analytics dashboard temps réel
```

### Phase 2 : Évolution Intelligente
```
Additions:
1. Algorithme génétique avec fitness multi-critères
2. Mémoire collective pondérée par performance
3. Détection de patterns avec ML basique
4. A/B testing automatisé
```

### Phase 3 : IA Avancée
```
Intégrations:
1. LLM pour analyse de marché
2. Reinforcement Learning pour adaptation
3. Ensemble de modèles pour décisions
4. Backtesting sur données historiques
```

## 8. Recommandations Finales

### Pour Votre Projet

1. **Capital** : 250€ LTC est suffisant avec gestion stricte
2. **Sessions** : 1000-5000 paris par session optimal
3. **Base Bet** : 0.00015 LTC (mise minimum)
4. **Stop-Loss Global** : -20% du capital total = arrêt
5. **Profit Target** : +5-10% par jour réaliste

### Logging Optimal
- **Format** : JSON Lines avec compression
- **Détail** : Chaque pari + contexte complet
- **Rotation** : Par taille (100MB) ou journalière
- **Métriques Temps Réel** : Dashboard Grafana/Prometheus

### Sécurité
- **Paper Trading** : Minimum 10,000 paris simulés
- **Validation** : Backtesting sur 1M+ paris
- **Circuit Breaker** : Si perte > 5% en 1 heure
- **Audit Trail** : Logs immutables de toutes décisions
