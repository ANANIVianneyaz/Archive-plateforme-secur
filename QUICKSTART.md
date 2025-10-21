# Guide de Démarrage Rapide 🚀

## Installation en 5 minutes

### 1. Installation des dépendances

```bash
cd plateforme_secure
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copier le fichier de configuration exemple
cp .env.example .env

# Générer une secret key sécurisée
python -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"

# Copier la sortie dans le fichier .env
```

### 3. Initialiser la base de données

```bash
python init_db.py
```

### 4. Lancer l'application

```bash
python run.py
```

L'application sera accessible sur : **http://127.0.0.1:5000**

---

## Test Rapide

### 1. Créer un compte
- Aller sur http://127.0.0.1:5000
- Cliquer sur "S'inscrire"
- Créer un compte (mot de passe : min 8 caractères, 1 majuscule, 1 minuscule, 1 chiffre)

### 2. Tester les fonctionnalités
- Créer un dossier
- Uploader un fichier
- Créer une note
- Créer une étiquette et l'associer à un dossier

---

## Vérification de Sécurité

### Test Injection SQL
```bash
# Tentez de vous connecter avec:
Username: admin' OR '1'='1' --
Password: anything

# Résultat attendu: Échec de connexion ✅
```

### Test XSS
```bash
# Créez une note avec le titre:
<script>alert('XSS')</script>

# Résultat attendu: Texte affiché tel quel, pas d'exécution ✅
```

### Test Path Traversal
```bash
# Tentez d'uploader un fichier nommé:
../../../etc/passwd

# Résultat attendu: Nom sanitizé automatiquement ✅
```

---

## Différences Clés avec la Version Vulnérable

✅ **Authentification sécurisée** : bcrypt au lieu de MD5  
✅ **Protection SQL** : Requêtes paramétrées  
✅ **Protection XSS** : Échappement automatique  
✅ **Protection CSRF** : Tokens sur tous les formulaires  
✅ **Rate Limiting** : Max 10 tentatives de connexion/heure  
✅ **Validation** : Tous les inputs validés  
✅ **Logs** : Tous les événements tracés  

---

## Structure des Fichiers

```
plateforme_secure/
├── app.py                 # Application principale (SÉCURISÉE)
├── config.py              # Configuration avec .env
├── requirements.txt       # Dépendances à jour
├── run.py                 # Script de démarrage
├── init_db.py             # Initialisation DB
├── .env.example           # Exemple de config
├── README.md              # Documentation complète
├── SECURITY.md            # Détail des corrections
└── QUICKSTART.md          # Ce fichier
```

---

## Production

Pour déployer en production :

```bash
# 1. Définir l'environnement
export FLASK_ENV=production
export SECRET_KEY=<votre_secret_key_genere>

# 2. Utiliser Gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app

# 3. Configurer Nginx comme reverse proxy
# 4. Activer HTTPS avec Let's Encrypt
```

---

## Support

Pour plus de détails, consultez :
- **README.md** : Documentation complète
- **SECURITY.md** : Détail de toutes les corrections de sécurité

---

**Version** : 2.0 Sécurisée  
**Statut** : ✅ Production Ready
