# app/extensions.py

import os
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail

jwt = JWTManager()
bcrypt = Bcrypt()
mail = Mail()

# Configuration de Flask-Limiter avec storage_uri
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
)
