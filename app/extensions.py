# app/extensions.py

import logging
import redis
from flask_mongoengine import MongoEngine
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail

db = MongoEngine()
jwt = JWTManager()
bcrypt = Bcrypt()
limiter = Limiter(key_func=get_remote_address)
mail = Mail()


try:
    redis_client = redis.StrictRedis(host=redis_host, port=redis_port, db=redis_db, decode_responses=True)
    # Tester la connexion à Redis
    redis_client.ping()
    logging.info("Connexion à Redis réussie.")
except redis.RedisError as e:
    logging.error(f"Erreur de connexion à Redis: {e}")
    redis_client = None  # Gestion alternative si Redis est indisponible

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
