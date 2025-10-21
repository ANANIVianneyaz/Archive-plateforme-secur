#!/usr/bin/env python3
"""Script de démarrage de l'application"""

import os
from app import app, init_db

if __name__ == '__main__':
    # Initialiser la base de données si elle n'existe pas
    if not os.path.exists('database.db'):
        print("Initialisation de la base de données...")
        init_db()
        print("✓ Base de données initialisée!")
    
    # Démarrer l'application
    env = os.environ.get('FLASK_ENV', 'development')
    
    if env == 'development':
        print("\n" + "="*50)
        print("  MODE DÉVELOPPEMENT")
        print("  Application disponible sur http://127.0.0.1:5000")
        print("="*50 + "\n")
        app.run(debug=True, host='127.0.0.1', port=5000)
    else:
        print("\n" + "="*50)
        print("  MODE PRODUCTION")
        print("  Utilisez Gunicorn: gunicorn -w 4 -b 0.0.0.0:5000 app:app")
        print("="*50 + "\n")
        app.run(debug=False, host='127.0.0.1', port=5000)
