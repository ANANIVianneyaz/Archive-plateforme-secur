# Configuration sécurisée - Archive Platform
import os
from dotenv import load_dotenv
import secrets

# Charger les variables d'environnement depuis .env
load_dotenv()

class Config:
    """Configuration de base"""
    
    # Secret key depuis variable d'environnement ou génération automatique
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    
    # Base de données
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///database.db')
    
    # Configuration de session
    SESSION_COOKIE_SECURE = True  # Cookies uniquement en HTTPS
    SESSION_COOKIE_HTTPONLY = True  # Protection XSS
    SESSION_COOKIE_SAMESITE = 'Lax'  # Protection CSRF
    PERMANENT_SESSION_LIFETIME = 7200  # 2 heures
    
    # Upload de fichiers
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}
    
    # Sécurité
    BCRYPT_LOG_ROUNDS = 12  # Coût de hachage bcrypt
    MAX_LOGIN_ATTEMPTS = 5
    ACCOUNT_LOCKOUT_DURATION = 1800  # 30 minutes en secondes
    
    # Rate limiting
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL', 'memory://')
    RATELIMIT_STRATEGY = 'fixed-window'
    
    # CSRF
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # Pas de limite de temps pour le token CSRF
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = 'logs/app.log'
    

class DevelopmentConfig(Config):
    """Configuration pour le développement"""
    DEBUG = True
    TESTING = False
    SESSION_COOKIE_SECURE = False  # HTTP autorisé en développement
    

class ProductionConfig(Config):
    """Configuration pour la production"""
    DEBUG = False
    TESTING = False
    
    # Variables obligatoires en production
    if not os.environ.get('SECRET_KEY'):
        raise ValueError("SECRET_KEY doit être défini en production")
    

class TestingConfig(Config):
    """Configuration pour les tests"""
    TESTING = True
    WTF_CSRF_ENABLED = False
    DATABASE_URL = 'sqlite:///:memory:'
    SESSION_COOKIE_SECURE = False
    

# Sélection de la configuration selon l'environnement
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(env=None):
    """Récupère la configuration appropriée"""
    if env is None:
        env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])
