# Utiliser une image de base Python
FROM python:3.8

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Copier les fichiers nécessaires dans le conteneur
COPY . /app

# Installer les dépendances Python à partir du fichier requirements.txt
RUN pip install -r requirements.txt

# Exposer le port sur lequel Flask s'exécutera
EXPOSE 5000

# Commande pour lancer l'application Flask
CMD ["python", "app.py"]
