# app/services/user.py

from app.models.user import User
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity
)

from flask import current_app
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from app.schemas.user import UserSchema
from marshmallow import ValidationError
import logging
from threading import Thread
from flask_mail import Message
from app.extensions import mail
from typing import Tuple, Dict, Any, Optional
from datetime import timedelta
from app.schemas.user import (
    ResetPasswordSchema
)

class UserService:
    """
    Service pour les opérations liées aux utilisateurs.
    """

    def register_user(self, username: str, email: str, password: str) -> Tuple[Dict[str, Any], int]:
        """
        Enregistre un nouvel utilisateur.

        :param username: Le nom d'utilisateur.
        :param email: L'adresse email.
        :param password: Le mot de passe.
        :return: Un tuple contenant la réponse JSON et le code HTTP.
        """
        if User.objects(username=username).first():
            return {'errors': 'Le nom d\'utilisateur est déjà pris.'}, 400
        if User.objects(email=email).first():
            return {'errors': 'Un compte avec cet email existe déjà.'}, 400
        user = User(username=username, email=email)
        user.set_password(password)
        user.save()
        return {'message': 'Utilisateur créé avec succès'}, 201

    def authenticate_user(self, username: str, password: str) -> Tuple[Dict[str, Any], int]:
        """
        Authentifie un utilisateur et génère des tokens JWT.

        :param username: Le nom d'utilisateur.
        :param password: Le mot de passe.
        :return: Un tuple contenant les tokens JWT et le code HTTP.
        """
        user = User.objects(username=username).first()
        if not user or not user.check_password(password):
            return {'errors': 'Nom d\'utilisateur ou mot de passe incorrect.'}, 401
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        return {'access_token': access_token, 'refresh_token': refresh_token}, 200

    def revoke_token(self, jti: str, token_type: str) -> None:
        """
        Révoque un token JWT en le stockant dans Redis.

        :param jti: L'identifiant unique du token.
        :param token_type: Le type du token ('access' ou 'refresh').
        """
        try:
            if token_type == 'access':
                expires = current_app.config['JWT_ACCESS_TOKEN_EXPIRES']
            elif token_type == 'refresh':
                expires = current_app.config['JWT_REFRESH_TOKEN_EXPIRES']
            else:
                expires = 3600  # Valeur par défaut d'une heure

            if isinstance(expires, timedelta):
                expires = int(expires.total_seconds())
            elif isinstance(expires, int):
                pass
            else:
                expires = 3600  # Valeur par défaut d'une heure

            redis_client = current_app.extensions.get('redis_client')
            if redis_client:
                redis_client.set(jti, 'true', ex=expires)
        except Exception as e:
            logging.error(f'Erreur lors de la révocation du token: {e}')

    # Méthode pour révoquer tous les tokens de l'utilisateur (par exemple lors de la réinitialisation du mot de passe)
    def revoke_all_tokens(self, user_id: str) -> None:
        """
        Révoque tous les tokens associés à un utilisateur.

        :param user_id: L'ID de l'utilisateur.
        """
        redis_client = current_app.extensions.get('redis_client')
        if redis_client:
            pattern = f"user_{user_id}_*"
            keys = redis_client.keys(pattern)
            for key in keys:
                redis_client.delete(key)

    def request_password_reset(self, email: str) -> Tuple[Dict[str, Any], int]:
        """
        Génère un token de réinitialisation et envoie un email à l'utilisateur.

        :param email: L'adresse email de l'utilisateur.
        :return: Un tuple contenant le message de confirmation et le code HTTP.
        """
        user = User.objects(email=email).first()
        if user:
            token = self.generate_password_reset_token(email)
            self.send_password_reset_email(email, token)
        return {'message': 'Si un compte avec cet email existe, un email de réinitialisation a été envoyé.'}, 200

    def generate_password_reset_token(self, identifier: str) -> str:
        """
        Génère un token sécurisé pour la réinitialisation du mot de passe.

        :param identifier: L'identifiant unique (email) de l'utilisateur.
        :return: Le token de réinitialisation.
        """
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return serializer.dumps(identifier, salt='password-reset-salt')

    def send_password_reset_email(self, email: str, token: str) -> None:
        """
        Envoie un email de réinitialisation de mot de passe à l'utilisateur.

        :param email: L'adresse email de l'utilisateur.
        :param token: Le token de réinitialisation.
        """
        try:
            reset_url = f"{current_app.config.get('FRONTEND_URL', 'http://localhost:3000')}/reset-password?token={token}"
            msg = Message(
                subject="Réinitialisation de votre mot de passe",
                sender=current_app.config['MAIL_DEFAULT_SENDER'],
                recipients=[email]
            )
            msg.body = (
                f"Pour réinitialiser votre mot de passe, cliquez sur le lien suivant : {reset_url}\n\n"
                "Si vous n'avez pas demandé cette réinitialisation, veuillez ignorer cet email."
            )
            # Envoi asynchrone de l'email (en production, utilisez une file de tâches comme Celery)
            Thread(target=mail.send, args=(msg,)).start()
            logging.info(f'Email de réinitialisation envoyé à {email}')
        except Exception as e:
            logging.error(f'Erreur lors de l\'envoi de l\'email de réinitialisation: {e}')

    def verify_password_reset_token(self, token: str, expiration: int = 3600) -> Optional[str]:
        """
        Vérifie la validité du token de réinitialisation.

        :param token: Le token de réinitialisation.
        :param expiration: Durée de validité du token en secondes.
        :return: L'email de l'utilisateur si le token est valide, None sinon.
        """
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            identifier = serializer.loads(token, salt='password-reset-salt', max_age=expiration)
            return identifier
        except SignatureExpired:
            logging.error('Token de réinitialisation de mot de passe expiré')
            return None
        except BadSignature:
            logging.error('Token de réinitialisation de mot de passe invalide')
            return None

    def reset_password(self, token: str, new_password: str) -> Tuple[Dict[str, Any], int]:
        """
        Réinitialise le mot de passe de l'utilisateur.

        :param token: Le token de réinitialisation.
        :param new_password: Le nouveau mot de passe.
        :return: Un tuple contenant le message de confirmation et le code HTTP.
        """
        email = self.verify_password_reset_token(token)
        if not email:
            return {'errors': 'Token invalide ou expiré.'}, 400
        user = User.objects(email=email).first()
        if not user:
            return {'errors': 'Utilisateur non trouvé.'}, 400
        try:
            # Validation du nouveau mot de passe
            data = {'password': new_password}
            password_field = ResetPasswordSchema().fields['password']
            password_field.deserialize(new_password)
        except ValidationError as err:
            return {'errors': err.messages}, 400
        user.set_password(new_password)
        user.save()
        return {'message': 'Mot de passe réinitialisé avec succès.'}, 200
