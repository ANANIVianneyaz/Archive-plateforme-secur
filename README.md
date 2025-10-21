# Archive Platform - Version Sécurisée 🔒

## 🎯 Aperçu

Cette version corrige **toutes les vulnérabilités de sécurité** présentes dans la version précédente tout en **préservant l'interface utilisateur identique**.

## ✅ Vulnérabilités Corrigées

### 1. **Injection SQL** ✔️
- **Avant** : Utilisation de f-strings pour construire les requêtes SQL
- **Après** : Utilisation de requêtes paramétrées (prepared statements)
```python
# Vulnérable
query = f"SELECT * FROM users WHERE username = '{username}'"

# Sécurisé
cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
```

### 2. **Hachage Faible des Mots de Passe** ✔️
- **Avant** : MD5 (facilement cassable)
- **Après** : bcrypt avec salt aléatoire
```python
# Vulnérable
password_hash = hashlib.md5(password.encode()).hexdigest()

# Sécurisé
password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
```

### 3. **Cross-Site Scripting (XSS)** ✔️
- **Avant** : Utilisation de `|safe` dans les templates
- **Après** : Échappement automatique de Jinja2
```html
<!-- Vulnérable -->
<h4>{{ note.title|safe }}</h4>

<!-- Sécurisé -->
<h4>{{ note['title'] }}</h4>
```

### 4. **Path Traversal** ✔️
- **Avant** : Pas de validation des noms de fichiers
- **Après** : Utilisation de `secure_filename()` et validation stricte
```python
# Sécurisé
original_filename = sanitize_filename(file.filename)
unique_filename = str(uuid.uuid4()) + '_' + original_filename
```

### 5. **IDOR (Insecure Direct Object References)** ✔️
- **Avant** : Pas de vérification de propriété des ressources
- **Après** : Vérification systématique avec `check_resource_ownership()`
```python
if not check_resource_ownership(user_id, 'file', file_id):
    flash('Accès non autorisé.', 'error')
    return redirect(url_for('dashboard'))
```

### 6. **Secrets Hardcodés** ✔️
- **Avant** : Secrets dans le code source
- **Après** : Variables d'environnement (.env)
```python
# Sécurisé
SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
```

### 7. **Protection CSRF** ✔️
- **Avant** : Aucune protection
- **Après** : Flask-WTF avec tokens CSRF
```html
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
```

### 8. **Rate Limiting** ✔️
- **Avant** : Pas de limitation
- **Après** : Flask-Limiter sur routes sensibles
```python
@app.route('/login', methods=['POST'])
@limiter.limit("10 per hour")
def login():
    # ...
```

### 9. **Protection Brute Force** ✔️
- **Avant** : Tentatives illimitées
- **Après** : Verrouillage de compte après 5 tentatives (30 min)

### 10. **Dépendances Obsolètes** ✔️
- **Avant** : Versions avec CVE connus
- **Après** : Dernières versions sécurisées

### 11. **Validation des Entrées** ✔️
- Validation stricte de tous les inputs utilisateur
- Contraintes de longueur et format
- Vérification des codes couleur hexadécimaux
- Validation des emails avec regex

### 12. **Sécurité des Sessions** ✔️
- Cookies HTTPS uniquement
- HttpOnly flag (protection XSS)
- SameSite flag (protection CSRF)
- Timeout de session (2 heures)

### 13. **Logging Sécurisé** ✔️
- Journalisation des événements de sécurité
- Rotation automatique des logs
- Pas de données sensibles dans les logs

### 14. **Content Security Policy** ✔️
- En-têtes CSP dans base.html
- Protection contre les injections de scripts

## 🛠️ Installation

### Prérequis
- Python 3.8+
- pip

### 1. Cloner et installer les dépendances

```bash
cd plateforme_secure
pip install -r requirements.txt
```

### 2. Configurer les variables d'environnement

```bash
# Copier le fichier exemple
cp .env.example .env

# Générer une secret key sécurisée
python -c "import secrets; print(secrets.token_hex(32))"

# Éditer .env et ajouter votre SECRET_KEY
```

### 3. Initialiser la base de données

```bash
python init_db.py
```

### 4. Lancer l'application

#### Mode Développement
```bash
python run.py
```

#### Mode Production (avec Gunicorn)
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## 📝 Structure du Projet

```
plateforme_secure/
├── app.py                 # Application Flask sécurisée
├── config.py              # Configuration avec gestion d'environnement
├── requirements.txt       # Dépendances à jour
├── run.py                 # Script de démarrage
├── init_db.py             # Initialisation de la base de données
├── .env.example           # Exemple de configuration
├── .gitignore             # Fichiers à ignorer
├── templates/
│   ├── base.html          # Template de base avec CSP
│   ├── dashboard.html     # Dashboard sans XSS
│   ├── login.html         # Formulaire avec CSRF
│   ├── register.html      # Validation stricte
│   └── ...
├── static/
│   ├── css/
│   └── js/
└── uploads/
```

## 🔐 Fonctionnalités de Sécurité

### Authentification
- Hachage bcrypt des mots de passe
- Validation force du mot de passe (8 caractères min, majuscule, minuscule, chiffre)
- Verrouillage de compte après 5 tentatives échouées
- Déverrouillage automatique après 30 minutes

### Protection des Données
- Toutes les requêtes SQL paramétrées
- Vérification de propriété sur toutes les ressources
- Validation stricte des entrées utilisateur
- Échappement automatique des sorties

### Sécurité des Fichiers
- Validation des extensions autorisées
- Sanitisation des noms de fichiers
- Limite de taille (16MB)
- Stockage sécurisé avec noms uniques (UUID)
- Vérification du chemin avant accès

### Protection des Sessions
- Cookies sécurisés (Secure, HttpOnly, SameSite)
- Timeout de 2 heures
- Régénération de session à la connexion

## 📊 Monitoring et Logging

Les logs sont stockés dans `logs/app.log` avec rotation automatique :
- Tentatives de connexion
- Actions sensibles
- Erreurs de sécurité
- Accès non autorisés

## 🚀 Déploiement en Production

### Configuration Requise

1. **Variables d'environnement obligatoires**
```bash
export FLASK_ENV=production
export SECRET_KEY=<votre_secret_key_genere>
```

2. **Serveur WSGI (Gunicorn)**
```bash
gunicorn -w 4 -b 0.0.0.0:8000 \
         --access-logfile logs/access.log \
         --error-logfile logs/error.log \
         app:app
```

3. **Reverse Proxy (Nginx)**
```nginx
server {
    listen 443 ssl http2;
    server_name votre-domaine.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

4. **HTTPS Obligatoire**
- Utiliser Let's Encrypt pour les certificats SSL
- Redirection HTTP vers HTTPS

## 🧑‍💻 Tests de Sécurité

### Tests Manuels

```bash
# Test injection SQL
# Essayez avec username: admin' OR '1'='1
# Résultat attendu : Échec de connexion

# Test XSS
# Créez une note avec: <script>alert('XSS')</script>
# Résultat attendu : Texte échappé, pas d'exécution

# Test Path Traversal  
# Tentez d'uploader un fichier nommé: ../../../etc/passwd
# Résultat attendu : Nom sanitizé

# Test IDOR
# Tentez d'accéder au fichier d'un autre utilisateur
# Résultat attendu : Accès refusé
```

## 📝 Comparaison Version Vulnérable vs Sécurisée

| Aspect | Version Vulnérable | Version Sécurisée |
|--------|---------------------|---------------------|
| Injection SQL | ❌ F-strings | ✅ Requêtes paramétrées |
| Mots de passe | ❌ MD5 | ✅ bcrypt |
| XSS | ❌ `|safe` | ✅ Échappement auto |
| CSRF | ❌ Aucune protection | ✅ Tokens CSRF |
| Path Traversal | ❌ Pas de validation | ✅ `secure_filename()` |
| IDOR | ❌ Pas de vérification | ✅ Vérification systématique |
| Rate Limiting | ❌ Aucune limite | ✅ Flask-Limiter |
| Secrets | ❌ Hardcodés | ✅ Variables d'env |
| Sessions | ❌ Non sécurisées | ✅ Secure/HttpOnly/SameSite |
| Dépendances | ❌ Obsolètes (CVE) | ✅ À jour |
| Debug | ❌ Activé en prod | ✅ Désactivé |
| Validation | ❌ Minimale | ✅ Stricte |
| Logging | ❌ Aucun | ✅ Complet |

## ⚠️ Notes Importantes

1. **Ne jamais committer le fichier `.env`** - Il contient des secrets
2. **Toujours utiliser HTTPS en production**
3. **Sauvegarder régulièrement la base de données**
4. **Surveiller les logs pour détecter les activités suspectes**
5. **Mettre à jour régulièrement les dépendances**

## 🔧 Maintenance

### Mise à jour des dépendances
```bash
pip list --outdated
pip install --upgrade <package>
```

### Rotation des logs
Les logs sont automatiquement rotationés (10 MB max, 10 fichiers)

### Sauvegarde de la base de données
```bash
sqlite3 database.db ".backup backup_$(date +%Y%m%d).db"
```

## 💬 Support

Pour toute question de sécurité, consultez :
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Flask Security Best Practices](https://flask.palletsprojects.com/en/latest/security/)

## 📜 Licence

Ce projet est fourni à des fins éducatives.

---

**Version** : 2.0 Sécurisée  
**Date** : 2025  
**Auteur** : MiniMax Agent
