# app/__init__.py

from flask import Flask, jsonify
from app.config import DevelopmentConfig, ProductionConfig, TestingConfig
import os
import logging
from werkzeug.exceptions import HTTPException

from app.extensions import db, jwt, bcrypt, limiter, mail
from flask_cors import CORS
import redis

def create_app(config_class=None):
    app = Flask(__name__)

    # Configuration de CORS
    CORS(app, resources={r"/*": {"origins": os.environ.get('FRONTEND_URL', '*')}}, supports_credentials=True)

    env = os.getenv('FLASK_ENV', 'development')

    if not config_class:
        if env == 'production':
            config_class = ProductionConfig
        elif env == 'testing':
            config_class = TestingConfig
        else:
            config_class = DevelopmentConfig

    app.config.from_object(config_class)

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

    # Fonction pour vérifier si un token est révoqué
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        jti = jwt_payload['jti']
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

    # Stocker redis_client dans les extensions de l'application
    app.extensions['redis_client'] = redis_client

    # Enregistrement des blueprints
    from app.controllers.user import user_bp
    app.register_blueprint(user_bp, url_prefix='/user')

    # Configuration de la journalisation
    logging.basicConfig(
        level=logging.INFO,
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
