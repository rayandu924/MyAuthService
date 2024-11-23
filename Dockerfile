# Dockerfile

# Étape 1 : Build des dépendances dans une image temporaire
FROM python:3.9-slim-buster AS builder

WORKDIR /app

# Installer les dépendances Python
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Étape 2 : Construire l'image finale
FROM python:3.9-slim-buster

WORKDIR /app

# Copier les dépendances Python depuis le builder
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copier le reste de l'application
COPY . .

# Créer un utilisateur non privilégié
RUN useradd -m appuser && chown -R appuser /app
USER appuser

# Variables d'environnement
ENV FLASK_APP=app/server.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Exposer le port de l'application
EXPOSE 5000

# Commande pour démarrer l'application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--access-logfile", "-", "--error-logfile", "-", "app.server:app"]
