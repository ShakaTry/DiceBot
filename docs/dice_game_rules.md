# Règles du Jeu Dice

## Principe de Base

Le jeu Dice est un jeu de hasard simple où :
1. Le joueur choisit un **multiplicateur** (ex: 2x, 3x, 10x...)
2. Le système génère un nombre aléatoire entre **0.00 et 99.99**
3. Le joueur gagne si le résultat est inférieur à son **seuil de victoire**

## Calcul du Seuil (avec House Edge)

### Calcul Théorique (sans edge)
```
Seuil_théorique = 100 / Multiplicateur
```

### Calcul Réel sur Bitsler (1% House Edge)
```
Seuil_réel = (100 / Multiplicateur) * 0.99
```

Exemples avec 1% house edge :
- Multiplicateur 2x → Seuil = 49.50 (au lieu de 50%)
- Multiplicateur 3x → Seuil = 33.00 (au lieu de 33.33%)
- Multiplicateur 10x → Seuil = 9.90 (au lieu de 10%)
- Multiplicateur 100x → Seuil = 0.99 (au lieu de 1%)

### Impact du House Edge
- Réduit les chances de gain de 1%
- Sur le long terme, garantit un avantage au casino
- Doit être pris en compte dans toute stratégie viable

## Mécaniques de Jeu

### Mise (Bet)
- Montant minimum/maximum défini par la plateforme
- Généralement en crypto-monnaie (BTC, ETH, etc.)

### Résultat
- **Victoire** : Nombre < Seuil → Gain = Mise × Multiplicateur
- **Défaite** : Nombre ≥ Seuil → Perte de la mise

### House Edge
- La plupart des sites ont un avantage maison de 1%
- Cela signifie que le multiplicateur réel est légèrement inférieur

## Stratégies Classiques

### 1. Martingale
- Doubler la mise après chaque perte
- Revenir à la mise initiale après une victoire
- Risqué mais populaire

### 2. Paroli (Martingale Inversée)
- Doubler après chaque victoire
- Revenir à la mise initiale après une perte

### 3. D'Alembert
- Augmenter la mise d'une unité après une perte
- Diminuer d'une unité après une victoire

### 4. Fibonacci
- Suivre la séquence de Fibonacci pour les mises
- Avancer dans la séquence après une perte
- Reculer de deux positions après une victoire

## Paramètres à Considérer

### Pour le Simulateur
1. **Seed** : Graine pour la génération aléatoire
2. **Bankroll** : Capital initial
3. **Limites** : Min/max de mise
4. **Sessions** : Nombre de parties à simuler

### Pour les Stratégies IA
1. **Agressivité** : Taille des mises par rapport au bankroll
2. **Seuil de Stop** : Quand arrêter (profit/perte)
3. **Adaptation** : Réaction aux séries de victoires/défaites
4. **Multiplicateur préféré** : Risque vs récompense

## Métriques de Performance

1. **ROI** (Return on Investment)
2. **Drawdown Maximum** : Plus grosse perte consécutive
3. **Ratio de Victoires** : % de parties gagnées
4. **Durée de Survie** : Nombre de parties avant faillite
5. **Volatilité** : Écart-type des résultats

## Système de Vault (Gestion du Capital)

### Concept
Séparer le capital total en deux parties :
- **Vault** : Réserve sécurisée (80-90% du capital)
- **Bankroll Active** : Capital de jeu pour les sessions (10-20%)

### Avantages du Vault
1. **Protection** : Limite les pertes maximales par session
2. **Psychologie** : Réduit la pression de jouer tout le capital
3. **Gestion** : Permet des stratégies plus agressives sur la bankroll active

### Règles de Transfert
- **Recharge** : Si bankroll < X%, transfert automatique depuis vault
- **Sécurisation** : Si profit > Y%, transfert vers vault
- **Limites** : Maximum Z transferts par période

### Exemple Pratique (250€ LTC)
```
Capital Total : 250€ LTC
├── Vault : 200€ (80%)
└── Bankroll Active : 50€ (20%)
    ├── Session 1 : 10€ (stop-loss -5€, take-profit +5€)
    ├── Session 2 : 10€
    └── Réserve : 30€
```

## Considérations Techniques

### Spécificités Bitsler
- **Mise minimum** : Variable selon la crypto (important pour LTC)
- **Vitesse** : ~1 pari/seconde maximum
- **API** : Pas d'API officielle (nécessite browser automation)
- **Limites** : Anti-bot detection à considérer

### Fairness
- Les sites utilisent souvent un système "Provably Fair"
- Hash cryptographique pour vérifier l'équité
- Important pour la simulation réaliste

### Latence
- Temps entre les paris (anti-spam)
- À considérer pour l'automatisation

### Limites de la Plateforme
- Mise minimum/maximum
- Limites de retrait
- Vérifications KYC
