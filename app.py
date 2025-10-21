from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, jsonify, abort
import sqlite3
import os
import bcrypt
import secrets
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import uuid
import re
from functools import wraps
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
import logging
from logging.handlers import RotatingFileHandler

# Configuration sécurisée
app = Flask(__name__)

# Génération de secret key sécurisée depuis les variables d'environnement
app.secret_key = os.environ.get('SECRET_KEY') or secrets.token_hex(32)

# Protection CSRF - Désactivée pour les tests
# csrf = CSRFProtect(app)
# À réactiver en production en décommentant la ligne ci-dessus

# Rate limiting pour prévenir les attaques par force brute
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Configuration upload sécurisée
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE
app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS uniquement
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Protection XSS
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Protection CSRF
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)  # Session timeout

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Configuration du logging
if not app.debug:
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Archive Platform startup')

def get_db_connection():
    """Crée une connexion sécurisée à la base de données"""
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row  # Permet d'accéder aux colonnes par nom
    return conn

def init_db():
    """Initialise la base de données SQLite avec des contraintes de sécurité"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Table des utilisateurs avec contraintes renforcées
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL CHECK(length(username) >= 3 AND length(username) <= 50),
            email TEXT UNIQUE NOT NULL CHECK(email LIKE '%_@_%._%'),
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            failed_login_attempts INTEGER DEFAULT 0,
            account_locked_until TIMESTAMP
        )
    ''')
    
    # Table des fichiers
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            original_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_size INTEGER,
            folder_id INTEGER,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (folder_id) REFERENCES folders (id) ON DELETE CASCADE
        )
    ''')
    
    # Table des dossiers
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS folders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL CHECK(length(name) >= 1 AND length(name) <= 100),
            parent_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (parent_id) REFERENCES folders (id) ON DELETE CASCADE
        )
    ''')
    
    # Table des notes avec validation
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL CHECK(length(title) >= 1 AND length(title) <= 200),
            content TEXT CHECK(length(content) <= 10000),
            folder_id INTEGER,
            user_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (folder_id) REFERENCES folders (id) ON DELETE SET NULL
        )
    ''')
    
    # Table des étiquettes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS labels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL CHECK(length(name) >= 1 AND length(name) <= 50),
            color TEXT NOT NULL CHECK(color GLOB '#[0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F]'),
            user_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')
    
    # Table de liaison dossiers-étiquettes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS folder_labels (
            folder_id INTEGER NOT NULL,
            label_id INTEGER NOT NULL,
            PRIMARY KEY (folder_id, label_id),
            FOREIGN KEY (folder_id) REFERENCES folders (id) ON DELETE CASCADE,
            FOREIGN KEY (label_id) REFERENCES labels (id) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()
    conn.close()

def login_required(f):
    """Décorateur pour protéger les routes nécessitant une authentification"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Veuillez vous connecter pour accéder à cette page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def validate_email(email):
    """Valide le format d'une adresse email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password_strength(password):
    """Valide la force d'un mot de passe"""
    if len(password) < 8:
        return False, "Le mot de passe doit contenir au moins 8 caractères"
    if not re.search(r'[A-Z]', password):
        return False, "Le mot de passe doit contenir au moins une majuscule"
    if not re.search(r'[a-z]', password):
        return False, "Le mot de passe doit contenir au moins une minuscule"
    if not re.search(r'[0-9]', password):
        return False, "Le mot de passe doit contenir au moins un chiffre"
    return True, ""

def validate_hex_color(color):
    """Valide qu'une couleur est un code hexadécimal valide"""
    pattern = r'^#[0-9a-fA-F]{6}$'
    return re.match(pattern, color) is not None

def allowed_file(filename):
    """Vérifie si l'extension du fichier est autorisée"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def sanitize_filename(filename):
    """Nettoie et sécurise un nom de fichier"""
    # Utilise secure_filename de Werkzeug
    secured = secure_filename(filename)
    # Limite la longueur
    if len(secured) > 100:
        name, ext = os.path.splitext(secured)
        secured = name[:95] + ext
    return secured

def check_resource_ownership(user_id, resource_type, resource_id):
    """Vérifie que l'utilisateur est propriétaire de la ressource (protection IDOR)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if resource_type == 'file':
        cursor.execute('SELECT user_id FROM files WHERE id = ?', (resource_id,))
    elif resource_type == 'folder':
        cursor.execute('SELECT user_id FROM folders WHERE id = ?', (resource_id,))
    elif resource_type == 'note':
        cursor.execute('SELECT user_id FROM notes WHERE id = ?', (resource_id,))
    elif resource_type == 'label':
        cursor.execute('SELECT user_id FROM labels WHERE id = ?', (resource_id,))
    else:
        conn.close()
        return False
    
    result = cursor.fetchone()
    conn.close()
    
    return result and result['user_id'] == user_id

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
# Rate limiting désactivé pour les tests - À réactiver en production
# @limiter.limit("10 per 15 minutes")
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        # Validation des entrées
        if not username or len(username) < 3 or len(username) > 50:
            flash('Le nom d\'utilisateur doit contenir entre 3 et 50 caractères.', 'error')
            return render_template('register.html')
        
        if not validate_email(email):
            flash('Adresse email invalide.', 'error')
            return render_template('register.html')
        
        is_strong, message = validate_password_strength(password)
        if not is_strong:
            flash(message, 'error')
            return render_template('register.html')
        
        # Hachage sécurisé avec bcrypt
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Requête paramétrée (protection contre l'injection SQL)
            cursor.execute(
                'INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
                (username, email, password_hash)
            )
            conn.commit()
            app.logger.info(f'New user registered: {username}')
            flash('Inscription réussie ! Vous pouvez maintenant vous connecter.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Ce nom d\'utilisateur ou email existe déjà.', 'error')
        finally:
            conn.close()
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
# Rate limiting désactivé pour les tests - À réactiver en production
# @limiter.limit("20 per 5 minutes")
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Veuillez remplir tous les champs.', 'error')
            return render_template('login.html')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Requête paramétrée (protection SQL injection)
        cursor.execute(
            'SELECT id, username, password, failed_login_attempts, account_locked_until FROM users WHERE username = ?',
            (username,)
        )
        user = cursor.fetchone()
        
        if user:
            # Vérification du verrouillage de compte
            if user['account_locked_until']:
                locked_until = datetime.fromisoformat(user['account_locked_until'])
                if datetime.now() < locked_until:
                    flash('Compte temporairement verrouillé. Réessayez plus tard.', 'error')
                    conn.close()
                    return render_template('login.html')
            
            # Vérification du mot de passe avec bcrypt
            if bcrypt.checkpw(password.encode('utf-8'), user['password']):
                # Réinitialiser les tentatives échouées
                cursor.execute(
                    'UPDATE users SET failed_login_attempts = 0, account_locked_until = NULL, last_login = ? WHERE id = ?',
                    (datetime.now(), user['id'])
                )
                conn.commit()
                
                # Créer la session
                session.clear()
                session['user_id'] = user['id']
                session['username'] = user['username']
                session.permanent = True
                
                app.logger.info(f'User logged in: {username}')
                conn.close()
                return redirect(url_for('dashboard'))
            else:
                # Incrémenter les tentatives échouées
                failed_attempts = user['failed_login_attempts'] + 1
                
                if failed_attempts >= 5:
                    # Verrouiller le compte pour 30 minutes
                    locked_until = datetime.now() + timedelta(minutes=30)
                    cursor.execute(
                        'UPDATE users SET failed_login_attempts = ?, account_locked_until = ? WHERE id = ?',
                        (failed_attempts, locked_until, user['id'])
                    )
                    flash('Trop de tentatives échouées. Compte verrouillé pour 30 minutes.', 'error')
                else:
                    cursor.execute(
                        'UPDATE users SET failed_login_attempts = ? WHERE id = ?',
                        (failed_attempts, user['id'])
                    )
                    flash('Nom d\'utilisateur ou mot de passe incorrect.', 'error')
                
                conn.commit()
        else:
            flash('Nom d\'utilisateur ou mot de passe incorrect.', 'error')
        
        conn.close()
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    username = session.get('username', 'Unknown')
    session.clear()
    app.logger.info(f'User logged out: {username}')
    flash('Vous avez été déconnecté avec succès.', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    folder_id = request.args.get('folder_id', type=int)
    
    # Si un folder_id est fourni, vérifier qu'il appartient à l'utilisateur
    if folder_id:
        if not check_resource_ownership(user_id, 'folder', folder_id):
            flash('Accès non autorisé à ce dossier.', 'error')
            return redirect(url_for('dashboard'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Récupérer le nom du dossier actuel si on est dans un dossier
    current_folder_name = None
    if folder_id:
        cursor.execute('SELECT name FROM folders WHERE id = ?', (folder_id,))
        folder_info = cursor.fetchone()
        if folder_info:
            current_folder_name = folder_info['name']
    
    # Récupérer les dossiers (requêtes paramétrées)
    if folder_id:
        cursor.execute('SELECT * FROM folders WHERE user_id = ? AND parent_id = ?', (user_id, folder_id))
    else:
        cursor.execute('SELECT * FROM folders WHERE user_id = ? AND parent_id IS NULL', (user_id,))
    folders = cursor.fetchall()
    
    # Récupérer les fichiers
    if folder_id:
        cursor.execute('SELECT * FROM files WHERE user_id = ? AND folder_id = ?', (user_id, folder_id))
    else:
        cursor.execute('SELECT * FROM files WHERE user_id = ? AND folder_id IS NULL', (user_id,))
    files = cursor.fetchall()
    
    # Récupérer les notes
    if folder_id:
        cursor.execute('SELECT * FROM notes WHERE user_id = ? AND folder_id = ?', (user_id, folder_id))
    else:
        cursor.execute('SELECT * FROM notes WHERE user_id = ? AND folder_id IS NULL', (user_id,))
    notes = cursor.fetchall()
    
    # Récupérer toutes les étiquettes de l'utilisateur
    cursor.execute('SELECT * FROM labels WHERE user_id = ?', (user_id,))
    user_labels = cursor.fetchall()
    
    # Récupérer les étiquettes des dossiers
    folder_labels = {}
    for folder in folders:
        cursor.execute('''
            SELECT l.* FROM labels l 
            JOIN folder_labels fl ON l.id = fl.label_id 
            WHERE fl.folder_id = ? AND l.user_id = ?
        ''', (folder['id'], user_id))
        folder_labels[folder['id']] = cursor.fetchall()
    
    conn.close()
    
    return render_template('dashboard.html', 
                         folders=folders, 
                         files=files, 
                         notes=notes,
                         user_labels=user_labels,
                         folder_labels=folder_labels,
                         current_folder=folder_id,
                         current_folder_name=current_folder_name)

@app.route('/create_folder', methods=['POST'])
@login_required
@limiter.limit("30 per hour")
def create_folder():
    user_id = session['user_id']
    folder_name = request.form.get('folder_name', '').strip()
    parent_id = request.form.get('parent_id', type=int)
    
    # Validation
    if not folder_name or len(folder_name) < 1 or len(folder_name) > 100:
        flash('Le nom du dossier doit contenir entre 1 et 100 caractères.', 'error')
        return redirect(url_for('dashboard', folder_id=parent_id))
    
    # Vérifier la propriété du dossier parent
    if parent_id and not check_resource_ownership(user_id, 'folder', parent_id):
        flash('Accès non autorisé à ce dossier parent.', 'error')
        return redirect(url_for('dashboard'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Requête paramétrée
        cursor.execute(
            'INSERT INTO folders (user_id, name, parent_id) VALUES (?, ?, ?)',
            (user_id, folder_name, parent_id)
        )
        conn.commit()
        flash('Dossier créé avec succès!', 'success')
    except sqlite3.IntegrityError as e:
        flash('Erreur lors de la création du dossier.', 'error')
        app.logger.error(f'Error creating folder: {e}')
    finally:
        conn.close()
    
    return redirect(url_for('dashboard', folder_id=parent_id))

@app.route('/upload', methods=['POST'])
@login_required
@limiter.limit("20 per hour")
def upload_file():
    if 'file' not in request.files:
        flash('Aucun fichier sélectionné', 'error')
        return redirect(url_for('dashboard'))
    
    file = request.files['file']
    folder_id = request.form.get('folder_id', type=int)
    
    if file.filename == '':
        flash('Aucun fichier sélectionné', 'error')
        return redirect(url_for('dashboard'))
    
    user_id = session['user_id']
    
    # Vérifier la propriété du dossier
    if folder_id and not check_resource_ownership(user_id, 'folder', folder_id):
        flash('Accès non autorisé à ce dossier.', 'error')
        return redirect(url_for('dashboard'))
    
    # Validation du fichier
    if not allowed_file(file.filename):
        flash('Type de fichier non autorisé.', 'error')
        return redirect(url_for('dashboard', folder_id=folder_id))
    
    # Sécurisation du nom de fichier (protection Path Traversal)
    original_filename = sanitize_filename(file.filename)
    unique_filename = str(uuid.uuid4()) + '_' + original_filename
    
    # Construction sécurisée du chemin
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    
    # Vérification de la taille
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    
    if file_size > MAX_FILE_SIZE:
        flash('Fichier trop volumineux (max 16MB).', 'error')
        return redirect(url_for('dashboard', folder_id=folder_id))
    
    file.seek(0)
    
    try:
        # Sauvegarde sécurisée du fichier
        file.save(file_path)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Requête paramétrée
        cursor.execute(
            'INSERT INTO files (user_id, filename, original_name, file_path, file_size, folder_id) VALUES (?, ?, ?, ?, ?, ?)',
            (user_id, unique_filename, original_filename, file_path, file_size, folder_id)
        )
        conn.commit()
        conn.close()
        
        flash('Fichier uploadé avec succès!', 'success')
    except Exception as e:
        # Nettoyage en cas d'erreur
        if os.path.exists(file_path):
            os.remove(file_path)
        flash('Erreur lors de l\'upload du fichier.', 'error')
        app.logger.error(f'Error uploading file: {e}')
    
    return redirect(url_for('dashboard', folder_id=folder_id))

@app.route('/download/<filename>')
@login_required
def download_file(filename):
    user_id = session['user_id']
    
    # Vérifier que le fichier appartient à l'utilisateur (protection IDOR + Path Traversal)
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        'SELECT file_path FROM files WHERE filename = ? AND user_id = ?',
        (filename, user_id)
    )
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        flash('Fichier non trouvé ou accès non autorisé.', 'error')
        abort(404)
    
    # Vérification supplémentaire du chemin pour éviter le path traversal
    safe_path = os.path.normpath(result['file_path'])
    upload_dir = os.path.normpath(app.config['UPLOAD_FOLDER'])
    
    if not safe_path.startswith(upload_dir):
        flash('Accès non autorisé.', 'error')
        abort(403)
    
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@app.route('/search')
@login_required
def search():
    query = request.args.get('q', '').strip()
    user_id = session['user_id']
    
    if not query or len(query) > 100:
        return jsonify({'files': []})
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Requête paramétrée avec LIKE sécurisé
    search_pattern = f'%{query}%'
    cursor.execute(
        'SELECT * FROM files WHERE user_id = ? AND original_name LIKE ?',
        (user_id, search_pattern)
    )
    files = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({'files': files})

@app.route('/delete_file/<int:file_id>', methods=['POST'])
@login_required
def delete_file(file_id):
    user_id = session['user_id']
    
    # Vérification de propriété (protection IDOR)
    if not check_resource_ownership(user_id, 'file', file_id):
        flash('Accès non autorisé.', 'error')
        return redirect(url_for('dashboard'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Récupérer le chemin du fichier
    cursor.execute('SELECT file_path FROM files WHERE id = ?', (file_id,))
    file_info = cursor.fetchone()
    
    if file_info:
        file_path = file_info['file_path']
        
        # Suppression physique sécurisée
        try:
            if os.path.exists(file_path):
                # Vérification du chemin avant suppression
                safe_path = os.path.normpath(file_path)
                upload_dir = os.path.normpath(app.config['UPLOAD_FOLDER'])
                
                if safe_path.startswith(upload_dir):
                    os.remove(file_path)
        except Exception as e:
            app.logger.error(f'Error deleting file: {e}')
        
        # Suppression de la base de données (requête paramétrée)
        cursor.execute('DELETE FROM files WHERE id = ?', (file_id,))
        conn.commit()
        flash('Fichier supprimé avec succès!', 'success')
    else:
        flash('Fichier non trouvé.', 'error')
    
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/delete_folder/<int:folder_id>', methods=['POST'])
@login_required
def delete_folder(folder_id):
    user_id = session['user_id']
    
    # Vérification de propriété (protection IDOR)
    if not check_resource_ownership(user_id, 'folder', folder_id):
        flash('Accès non autorisé.', 'error')
        return redirect(url_for('dashboard'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Supprimer les fichiers physiques du dossier
    cursor.execute('SELECT file_path FROM files WHERE folder_id = ?', (folder_id,))
    files = cursor.fetchall()
    
    for file in files:
        try:
            if os.path.exists(file['file_path']):
                safe_path = os.path.normpath(file['file_path'])
                upload_dir = os.path.normpath(app.config['UPLOAD_FOLDER'])
                if safe_path.startswith(upload_dir):
                    os.remove(file['file_path'])
        except Exception as e:
            app.logger.error(f'Error deleting file: {e}')
    
    # Les suppressions en cascade sont gérées par les contraintes FK
    cursor.execute('DELETE FROM folders WHERE id = ?', (folder_id,))
    conn.commit()
    conn.close()
    
    flash('Dossier supprimé avec succès!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/create_note', methods=['POST'])
@login_required
@limiter.limit("50 per hour")
def create_note():
    user_id = session['user_id']
    title = request.form.get('note_title', '').strip()
    content = request.form.get('note_content', '').strip()
    folder_id = request.form.get('folder_id', type=int)
    
    # Validation
    if not title or len(title) < 1 or len(title) > 200:
        flash('Le titre doit contenir entre 1 et 200 caractères.', 'error')
        return redirect(url_for('dashboard', folder_id=folder_id))
    
    if content and len(content) > 10000:
        flash('Le contenu ne peut pas dépasser 10000 caractères.', 'error')
        return redirect(url_for('dashboard', folder_id=folder_id))
    
    # Vérifier la propriété du dossier
    if folder_id and not check_resource_ownership(user_id, 'folder', folder_id):
        flash('Accès non autorisé à ce dossier.', 'error')
        return redirect(url_for('dashboard'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Requête paramétrée (les données sont automatiquement échappées)
        cursor.execute(
            'INSERT INTO notes (title, content, folder_id, user_id) VALUES (?, ?, ?, ?)',
            (title, content, folder_id, user_id)
        )
        conn.commit()
        flash('Note créée avec succès!', 'success')
    except Exception as e:
        flash('Erreur lors de la création de la note.', 'error')
        app.logger.error(f'Error creating note: {e}')
    finally:
        conn.close()
    
    return redirect(url_for('dashboard', folder_id=folder_id))

@app.route('/edit_note/<int:note_id>', methods=['POST'])
@login_required
def edit_note(note_id):
    user_id = session['user_id']
    
    # Vérification de propriété
    if not check_resource_ownership(user_id, 'note', note_id):
        flash('Accès non autorisé.', 'error')
        return redirect(url_for('dashboard'))
    
    title = request.form.get('note_title', '').strip()
    content = request.form.get('note_content', '').strip()
    
    # Validation
    if not title or len(title) < 1 or len(title) > 200:
        flash('Le titre doit contenir entre 1 et 200 caractères.', 'error')
        return redirect(url_for('dashboard'))
    
    if content and len(content) > 10000:
        flash('Le contenu ne peut pas dépasser 10000 caractères.', 'error')
        return redirect(url_for('dashboard'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Requête paramétrée
    cursor.execute(
        'UPDATE notes SET title = ?, content = ?, updated_at = ? WHERE id = ?',
        (title, content, datetime.now(), note_id)
    )
    conn.commit()
    conn.close()
    
    flash('Note modifiée avec succès!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/delete_note/<int:note_id>', methods=['POST'])
@login_required
def delete_note(note_id):
    user_id = session['user_id']
    
    # Vérification de propriété (protection IDOR)
    if not check_resource_ownership(user_id, 'note', note_id):
        flash('Accès non autorisé.', 'error')
        return redirect(url_for('dashboard'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM notes WHERE id = ?', (note_id,))
    conn.commit()
    conn.close()
    
    flash('Note supprimée avec succès!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/create_label', methods=['POST'])
@login_required
@limiter.limit("20 per hour")
def create_label():
    user_id = session['user_id']
    name = request.form.get('label_name', '').strip()
    color = request.form.get('label_color', '').strip()
    
    # Validation stricte
    if not name or len(name) < 1 or len(name) > 50:
        flash('Le nom de l\'étiquette doit contenir entre 1 et 50 caractères.', 'error')
        return redirect(url_for('dashboard'))
    
    if not validate_hex_color(color):
        flash('Couleur invalide. Utilisez un code hexadécimal valide (ex: #FF5733).', 'error')
        return redirect(url_for('dashboard'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            'INSERT INTO labels (name, color, user_id) VALUES (?, ?, ?)',
            (name, color, user_id)
        )
        conn.commit()
        flash('Étiquette créée avec succès!', 'success')
    except Exception as e:
        flash('Erreur lors de la création de l\'étiquette.', 'error')
        app.logger.error(f'Error creating label: {e}')
    finally:
        conn.close()
    
    return redirect(url_for('dashboard'))

@app.route('/add_label_to_folder', methods=['POST'])
@login_required
def add_label_to_folder():
    user_id = session['user_id']
    folder_id = request.form.get('folder_id', type=int)
    label_id = request.form.get('label_id', type=int)
    
    if not folder_id or not label_id:
        flash('Données invalides.', 'error')
        return redirect(url_for('dashboard'))
    
    # Vérification de propriété des deux ressources
    if not check_resource_ownership(user_id, 'folder', folder_id):
        flash('Accès non autorisé au dossier.', 'error')
        return redirect(url_for('dashboard'))
    
    if not check_resource_ownership(user_id, 'label', label_id):
        flash('Accès non autorisé à l\'étiquette.', 'error')
        return redirect(url_for('dashboard'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            'INSERT OR IGNORE INTO folder_labels (folder_id, label_id) VALUES (?, ?)',
            (folder_id, label_id)
        )
        conn.commit()
        flash('Étiquette ajoutée au dossier!', 'success')
    except Exception as e:
        flash('Erreur lors de l\'ajout de l\'étiquette.', 'error')
        app.logger.error(f'Error adding label to folder: {e}')
    finally:
        conn.close()
    
    return redirect(url_for('dashboard'))

@app.route('/remove_label_from_folder', methods=['POST'])
@login_required
def remove_label_from_folder():
    user_id = session['user_id']
    folder_id = request.form.get('folder_id', type=int)
    label_id = request.form.get('label_id', type=int)
    
    if not folder_id or not label_id:
        flash('Données invalides.', 'error')
        return redirect(url_for('dashboard'))
    
    # Vérification de propriété
    if not check_resource_ownership(user_id, 'folder', folder_id):
        flash('Accès non autorisé.', 'error')
        return redirect(url_for('dashboard'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        'DELETE FROM folder_labels WHERE folder_id = ? AND label_id = ?',
        (folder_id, label_id)
    )
    conn.commit()
    conn.close()
    
    flash('Étiquette retirée du dossier!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/get_labels')
@login_required
def get_labels():
    user_id = session['user_id']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM labels WHERE user_id = ?', (user_id,))
    labels = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({'labels': labels})

@app.route('/vulnerabilities')
def vulnerabilities():
    return render_template('vulnerabilities.html')

# Gestionnaire d'erreurs
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(403)
def forbidden(e):
    return render_template('403.html'), 403

@app.errorhandler(500)
def internal_error(e):
    app.logger.error(f'Internal error: {e}')
    return render_template('500.html'), 500

if __name__ == '__main__':
    init_db()
    # Mode debug DÉSACTIVÉ en production
    # Utiliser un serveur WSGI comme Gunicorn en production
    app.run(debug=False, host='127.0.0.1', port=5000)
