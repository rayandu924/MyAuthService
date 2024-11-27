# Dockerfile

# Étape 1 : Build des dépendances dans une image temporaire
FROM python:3.11-slim AS builder

WORKDIR /app

# Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libssl-dev libffi-dev && \
    rm -rf /var/lib/apt/lists/*

# Copier les fichiers de configuration
COPY requirements.txt .

# Créer un virtualenv
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Installer les dépendances Python
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Étape 2 : Construire l'image finale
FROM python:3.11-slim

WORKDIR /app

# Copier le virtualenv depuis le builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copier le reste de l'application
COPY . .

# Create a non-privileged user and adjust ownership
RUN useradd -m appuser && chown -R appuser /app /opt/venv
USER appuser

# Variables d'environnement
ENV PYTHONUNBUFFERED=1

# Exposer le port de l'application
EXPOSE 5000

# Commande pour démarrer l'application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--access-logfile", "-", "--error-logfile", "-", "app.server:app"]
