# Dockerfile

FROM python:3.9-slim-buster

# Mettre à jour le système et installer les dépendances nécessaires en une seule couche
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Créer un environnement utilisateur non privilégié avant de copier les fichiers
RUN useradd -m appuser
USER appuser

WORKDIR /home/appuser/app

# Copier uniquement les fichiers nécessaires
COPY --chown=appuser:appuser requirements.txt ./

# Installer les dépendances Python
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copier le reste de l'application
COPY --chown=appuser:appuser . .

# Variables d'environnement
ENV FLASK_APP=server.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Exposer le port de l'application
EXPOSE 5000

# Commande pour démarrer l'application
CMD ["gunicorn", "--factory", "server:create_app", "--bind", "0.0.0.0:5000", "--workers", "4"]
