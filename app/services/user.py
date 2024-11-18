# app/services/user.py

from app.models.user import User
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
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

class UserService:
    """
    Service pour les opérations liées aux utilisateurs
    """

    def register_user(self, username: str, email: str, password: str) -> Tuple[Dict[str, Any], int]:
        if User.objects(username=username).first():
            return {'errors': 'Le nom d\'utilisateur est déjà pris.'}, 400
        if User.objects(email=email).first():
            return {'errors': 'Un compte avec cet email existe déjà.'}, 400
        user = User(username=username, email=email)
        user.set_password(password)
        user.save()
        return {'message': 'Utilisateur créé avec succès'}, 201

    def authenticate_user(self, username: str, password: str) -> Tuple[Dict[str, Any], int]:
        user = User.objects(username=username).first()
        if not user or not user.check_password(password):
            return {'errors': 'Nom d\'utilisateur ou mot de passe incorrect.'}, 401
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        return {'access_token': access_token, 'refresh_token': refresh_token}, 200

    def revoke_token(self, jti: str) -> None:
        try:
            expires = current_app.config['JWT_ACCESS_TOKEN_EXPIRES']
            redis_client = current_app.extensions.get('redis_client')
            if redis_client:
                redis_client.set(jti, 'true', ex=expires)
        except Exception as e:
            logging.error(f'Erreur lors de la révocation du token: {e}')

    def request_password_reset(self, email: str) -> Tuple[Dict[str, Any], int]:
        user = User.objects(email=email).first()
        if user:
            token = self.generate_password_reset_token(email)
            self.send_password_reset_email(email, token)
        return {'message': 'Si un compte avec cet email existe, un email de réinitialisation a été envoyé.'}, 200

    def generate_password_reset_token(self, identifier: str) -> str:
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return serializer.dumps(identifier, salt='password-reset-salt')

    def send_password_reset_email(self, email: str, token: str) -> None:
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
            Thread(target=mail.send, args=(msg,)).start()  # Envoi asynchrone
            logging.info(f'Email de réinitialisation envoyé à {email}')
        except Exception as e:
            logging.error(f'Erreur lors de l\'envoi de l\'email de réinitialisation: {e}')

    def verify_password_reset_token(self, token: str, expiration: int = 3600) -> Optional[str]:
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            identifier = serializer.loads(token, salt='password-reset-salt', max_age=expiration)
        except (SignatureExpired, BadSignature):
            if SignatureExpired:
                raise SignatureExpired('Token de réinitialisation de mot de passe expiré')
            else:
                raise BadSignature('Token de réinitialisation de mot de passe invalide')
        return identifier

    def reset_password(self, token: str, new_password: str) -> Tuple[Dict[str, Any], int]:
        try:
            email = self.verify_password_reset_token(token)
        except (SignatureExpired, BadSignature) as e:
            return {'errors': str(e)}, 400
        user = User.objects(email=email).first()
        if not user:
            return {'errors': 'Utilisateur non trouvé.'}, 400
        try:
            data = UserSchema().load({'password': new_password}, partial=('username', 'email'))
        except ValidationError as err:
            return {'errors': err.messages}, 400
        user.set_password(new_password)
        user.save()
        return {'message': 'Mot de passe réinitialisé avec succès.'}, 200
