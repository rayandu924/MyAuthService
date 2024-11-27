# app/config.py

import os
from datetime import timedelta
from distutils.util import strtobool

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'vous-devriez-changer-cette-clé')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'vous-devriez-changer-cette-clé-aussi')

    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', 3600)))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(seconds=int(os.environ.get('JWT_REFRESH_TOKEN_EXPIRES', 86400)))

    # Durée de validité du one-time code en secondes
    ONE_TIME_CODE_EXPIRATION = int(os.environ.get('ONE_TIME_CODE_EXPIRATION', 600))

    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Configuration Redis
    REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
    REDIS_DB = int(os.environ.get('REDIS_DB', 0))
    REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', None)
    REDIS_DECODE_RESPONSES = True  # Pour obtenir des chaînes de caractères

    # Construction de l'URL Redis
    if REDIS_PASSWORD:
        REDIS_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
    else:
        REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

    # Configuration Mail
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.example.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = bool(strtobool(os.environ.get('MAIL_USE_TLS', 'True')))
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')

    # URL du Frontend
    FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000')

    # Niveau de log
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
    LOG_FILE = os.environ.get('LOG_FILE', 'app.log')
    MAX_LOG_SIZE = int(os.environ.get('MAX_LOG_SIZE', 10 * 1024 * 1024))
    BACKUP_COUNT = int(os.environ.get('BACKUP_COUNT', 5))

    # URI MongoDB avec uuidRepresentation pour éliminer le warning
    MONGO_URI = os.environ.get(
        'MONGO_URI',
        'mongodb://root:example@localhost:27017/auth_service_db?authSource=admin&uuidRepresentation=standard'
    )

class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False

class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True

class TestingConfig(Config):
    TESTING = True
    SESSION_COOKIE_SECURE = False
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(seconds=30)  # Par exemple, 30 secondes pour les tests
    MAIL_SUPPRESS_SEND = True
    MONGO_URI = os.environ.get(
        'MONGO_URI',
        'mongodb://root:example@localhost:27017/test_auth_service_db?authSource=admin&uuidRepresentation=standard'
    )
