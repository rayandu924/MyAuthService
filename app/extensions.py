# app/extensions.py

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
    storage_uri="redis://redis:6379/0"  # Assurez-vous que l'URL correspond à votre configuration Redis
)
