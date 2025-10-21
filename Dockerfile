FROM python:3.11-slim

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Copier l'application
COPY . .

# Créer les répertoires nécessaires
RUN mkdir -p uploads logs

# Définir les variables d'environnement
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Exposer le port
EXPOSE 5000

# Initialiser la base de données au démarrage
RUN python init_db.py

# Commande de démarrage avec Gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
