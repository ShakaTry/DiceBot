# 🔑 Configuration des Tokens - Guide Complet

## 1️⃣ GitHub Personal Access Token

### Étapes de création :

1. **Aller sur GitHub** : https://github.com/settings/tokens
2. **Generate new token (classic)**
3. **Nom** : `DiceBot Integration`
4. **Expiration** : `90 days` (ou plus si tu veux)
5. **Scopes requis** :
   - ✅ `repo` - Full control of private repositories
   - ✅ `public_repo` - Access public repositories (si ton repo est public)
   - ✅ `write:issues` - Create and edit issues
   - ✅ `read:issues` - Read issues

### Configuration :
```bash
# Ajouter à ton .bashrc ou .zshrc
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export GITHUB_OWNER="ShakaTry"
export GITHUB_REPO="DiceBot"

# Ou créer un fichier .env
echo "GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" >> .env
echo "GITHUB_OWNER=ShakaTry" >> .env
echo "GITHUB_REPO=DiceBot" >> .env
```

### Test rapide :
```bash
# Tester l'accès GitHub
curl -H "Authorization: Bearer $GITHUB_TOKEN" \
     https://api.github.com/repos/ShakaTry/DiceBot/issues
```

---

## 2️⃣ Slack App Configuration

### A. Créer l'App Slack

1. **Aller sur** : https://api.slack.com/apps
2. **Create New App** → **From scratch**
3. **App Name** : `DiceBot`
4. **Workspace** : Ton workspace de dev

### B. Configurer les Permissions (OAuth & Permissions)

**Bot Token Scopes requis :**
```
✅ app_mentions:read    - Lire les mentions du bot
✅ channels:read        - Lire les informations des channels
✅ chat:write          - Envoyer des messages
✅ commands            - Utiliser les slash commands
✅ im:read             - Lire les messages privés
✅ users:read          - Lire les informations des utilisateurs
```

### C. Event Subscriptions

**Enable Events** et ajouter **Request URL** :
```
https://your-server.com/slack/events
```

**Subscribe to bot events :**
```
✅ app_mention     - Quand le bot est mentionné
✅ message.im      - Messages privés au bot
```

### D. Slash Commands

Créer ces commandes qui pointent vers `https://your-server.com/slack/commands` :

| Command | Description |
|---------|-------------|
| `/dicebot-status` | Afficher le statut du système |
| `/dicebot-simulate` | Lancer une simulation |
| `/dicebot-results` | Voir les derniers résultats |
| `/issue` | Gérer les issues GitHub |

### E. Installation

1. **Install App to Workspace**
2. **Copier les tokens** :
   - `Bot User OAuth Token` (commence par `xoxb-`)
   - `Signing Secret` (dans Basic Information)

### Configuration des variables :
```bash
# Tokens Slack
export SLACK_BOT_TOKEN="xoxb-xxxxxxxxxxxx-xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx"
export SLACK_SIGNING_SECRET="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/xxx/xxx/xxx"  # Optionnel
```

---

## 3️⃣ Serveur pour Événements Slack

### Option A - Local avec ngrok (développement)

```bash
# Installer ngrok
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok

# Authentifier ngrok (crée un compte sur ngrok.com)
ngrok authtoken YOUR_NGROK_TOKEN

# Démarrer le serveur DiceBot
python -m dicebot.integrations.slack_server --debug

# Dans un autre terminal, exposer via ngrok
ngrok http 3000
```

**URL ngrok** → Utiliser dans la config Slack (ex: `https://abc123.ngrok.io/slack/events`)

### Option B - Déploiement Cloud

#### Railway.app (recommandé)
```bash
# Installer Railway CLI
npm install -g @railway/cli

# Login
railway login

# Deployer
railway new
railway add
railway deploy
```

#### Heroku
```bash
# Créer Procfile
echo "web: python -m dicebot.integrations.slack_server --host 0.0.0.0 --port $PORT" > Procfile

# Deployer
heroku create dicebot-slack
heroku config:set GITHUB_TOKEN=xxx SLACK_BOT_TOKEN=xxx SLACK_SIGNING_SECRET=xxx
git push heroku main
```

---

## 4️⃣ Test de l'Intégration Complète

### Test GitHub
```python
from dicebot.integrations import GitHubClient

# Test basique
client = GitHubClient("ghp_xxx", "ShakaTry", "DiceBot")
result = client.get_issues(state="open", limit=5)
print(f"Issues ouvertes : {result['count']}")
```

### Test Slack
```bash
# Tester dans Slack :
@dicebot status
/issue list open
/issue create "Test depuis Slack" "Ceci est un test"
```

### Test complet
```bash
# Vérifier toutes les variables
env | grep -E "(GITHUB|SLACK)"

# Démarrer le serveur
python -m dicebot.integrations.slack_server

# Dans Slack, tester :
/issue create "Bug Fibonacci" "La stratégie plante après 10 pertes"
```

---

## 🚨 Sécurité

### Variables d'environnement (.env)
```bash
# Créer .env (jamais commité)
cat > .env << EOF
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GITHUB_OWNER=ShakaTry
GITHUB_REPO=DiceBot
SLACK_BOT_TOKEN=xoxb-xxxxxxxxxxxx-xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx
SLACK_SIGNING_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx/xxx/xxx
EOF

# Ajouter .env au .gitignore
echo ".env" >> .gitignore
```

### GitHub Secrets (pour Actions)
```bash
# Ajouter dans GitHub → Settings → Secrets :
GITHUB_TOKEN=xxx
SLACK_BOT_TOKEN=xxx  
SLACK_SIGNING_SECRET=xxx
SLACK_WEBHOOK_URL=xxx
```

---

## 📋 Checklist de Validation

- [ ] GitHub token créé avec les bons scopes
- [ ] Slack app créée et configurée
- [ ] Permissions Slack ajoutées
- [ ] Slash commands configurés
- [ ] Serveur démarré et accessible
- [ ] Event subscriptions configurées
- [ ] Variables d'environnement définies
- [ ] Test GitHub API réussi
- [ ] Test Slack commandes réussi
- [ ] Test intégration complète réussi

**Temps estimé total : 30-45 minutes** ⏱️
