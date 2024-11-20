# app/__init__.py

from flask import Flask, jsonify
from app.config import DevelopmentConfig, ProductionConfig, TestingConfig
import os
import logging
from werkzeug.exceptions import HTTPException

from app.extensions import db, jwt, bcrypt, limiter, mail
from flask_cors import CORS
import redis
import logging
from logging.handlers import RotatingFileHandler

def create_app(config_class=None):
    """
    Crée et configure l'application Flask.

    :param config_class: La classe de configuration à utiliser.
    :return: L'application Flask configurée.
    """
    app = Flask(__name__)

    # Configuration de CORS avec origines explicitement spécifiées
    CORS(app, resources={r"/*": {"origins": [os.environ.get('FRONTEND_URL', 'http://localhost:3000')]}},
         supports_credentials=True)

    env = os.getenv('FLASK_ENV', 'development')

    if not config_class:
        if env == 'production':
            config_class = ProductionConfig
        elif env == 'testing':
            config_class = TestingConfig
        else:
            config_class = DevelopmentConfig

    app.config.from_object(config_class)

    # ** Configuration avancée de la journalisation **
    log_level = app.config.get('LOG_LEVEL', 'INFO').upper()
    log_filename = app.config.get('LOG_FILE', 'app.log')
    max_log_size = int(app.config.get('MAX_LOG_SIZE', 10 * 1024 * 1024))  # 10 MB par défaut
    backup_count = int(app.config.get('BACKUP_COUNT', 5))  # 5 fichiers de sauvegarde par défaut

    # Configuration du gestionnaire de rotation des fichiers de logs
    handler = RotatingFileHandler(log_filename, maxBytes=max_log_size, backupCount=backup_count)
    handler.setLevel(log_level)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')
    handler.setFormatter(formatter)

    # Ajout du gestionnaire à l'application Flask
    app.logger.addHandler(handler)

    # Configuration de MongoEngine
    app.config['MONGODB_SETTINGS'] = {
        'host': app.config['MONGO_URI']
    }

    # Initialisation des extensions
    db.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)
    limiter.init_app(app)
    mail.init_app(app)

    # Initialisation du client Redis
    try:
        redis_client = redis.Redis(
            host=app.config['REDIS_HOST'],
            port=app.config['REDIS_PORT'],
            db=app.config['REDIS_DB'],
            decode_responses=True
        )
        redis_client.ping()
        logging.info("Connexion à Redis réussie.")
    except redis.RedisError as e:
        logging.error(f"Erreur de connexion à Redis: {e}")
        redis_client = None

    # Stocker redis_client dans les extensions de l'application
    app.extensions['redis_client'] = redis_client

    # Fonction pour vérifier si un token est révoqué
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        jti = jwt_payload['jti']
        redis_client = app.extensions.get('redis_client')
        if redis_client:
            try:
                entry = redis_client.get(jti)
                return entry == 'true'
            except Exception as e:
                logging.error(f'Erreur lors de la vérification du token: {e}')
                return True  # Considérer le token comme révoqué en cas d'erreur
        else:
            logging.warning("Redis client non disponible. Tous les tokens sont considérés comme révoqués.")
            return True

    # Enregistrement des blueprints
    from app.controllers.user import user_bp
    app.register_blueprint(user_bp, url_prefix='/user')

    # Configuration avancée de la journalisation (Suggestion 17)
    log_level = app.config.get('LOG_LEVEL', 'INFO').upper()
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )

    # Gestion des erreurs HTTP
    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        return jsonify({'error': e.description}), e.code

    # Gestion des autres exceptions
    @app.errorhandler(Exception)
    def handle_general_exception(e):
        logging.exception('Une erreur est survenue:')
        return jsonify({'error': 'Une erreur interne est survenue.'}), 500

    return app
