# app/config.py

import os
from dotenv import load_dotenv
from distutils.util import strtobool
from datetime import timedelta

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY n'est pas défini dans les variables d'environnement.")

    MONGO_URI = os.environ.get('MONGO_URI')
    if not MONGO_URI:
        raise ValueError("MONGO_URI n'est pas défini dans les variables d'environnement.")

    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    if not JWT_SECRET_KEY:
        raise ValueError("JWT_SECRET_KEY n'est pas défini dans les variables d'environnement.")

    try:
        JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', 3600)))
        JWT_REFRESH_TOKEN_EXPIRES = timedelta(seconds=int(os.environ.get('JWT_REFRESH_TOKEN_EXPIRES', 86400)))
    except ValueError:
        JWT_ACCESS_TOKEN_EXPIRES = 3600  # Valeur par défaut si la conversion échoue

    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Configuration Redis
    REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
    REDIS_DB = int(os.environ.get('REDIS_DB', 0))

    # Configuration Mail
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.example.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = bool(strtobool(os.environ.get('MAIL_USE_TLS', 'True')))
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')

    # URL du Frontend
    FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000')

class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False

class ProductionConfig(Config):
    DEBUG = False

class TestingConfig(Config):
    TESTING = True
    MONGO_URI = 'mongodb://localhost:27017/testdb'
    JWT_ACCESS_TOKEN_EXPIRES = 1  # Expiration rapide pour les tests
    MAIL_SUPPRESS_SEND = True  # Ne pas envoyer d'emails pendant les tests
