# Dockerfile

# Étape 1 : Build des dépendances dans une image temporaire
FROM python:3.9-slim-buster AS builder

# Créer un utilisateur non privilégié et configurer le WORKDIR
RUN useradd -m appuser
USER appuser
WORKDIR /home/appuser/app

# Installer les dépendances Python
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --user --no-cache-dir -r requirements.txt

# Étape 2 : Construire l'image finale
FROM python:3.9-slim-buster

# Créer un utilisateur non privilégié
RUN useradd -m appuser
USER appuser

WORKDIR /home/appuser/app

# Copier les dépendances Python depuis le builder
COPY --from=builder /home/appuser/.local /home/appuser/.local

# Mettre à jour le PATH pour inclure les paquets installés localement
ENV PATH="/home/appuser/.local/bin:${PATH}"

# Copier le reste de l'application
COPY --chown=appuser:appuser . .

# Variables d'environnement
ENV FLASK_APP=server.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Exposer le port de l'application
EXPOSE 5000

# Commande pour démarrer l'application
CMD ["gunicorn", "server:create_app()", "--bind", "0.0.0.0:5000", "--workers", "4", "--access-logfile", "-", "--error-logfile", "-"]
