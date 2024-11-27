# app/services/user.py

from app.models.user import User
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    decode_token
)
from flask import current_app
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from app.schemas.user import ResetPasswordSchema
from marshmallow import ValidationError
import logging
from threading import Thread
from flask_mail import Message
from typing import Tuple, Dict, Any, Optional
from datetime import datetime
from mongoengine import Q
import random
from app.extensions import mail

class UserService:
    """
    Service pour les opérations liées aux utilisateurs.
    """

    def register_user(self, username: str, email: str, password: str) -> Tuple[Dict[str, Any], int]:
        """
        Enregistre un nouvel utilisateur.
        """
        if User.objects(username=username).first():
            return {'errors': 'Le nom d\'utilisateur est déjà pris.'}, 400
        if User.objects(email=email).first():
            return {'errors': 'Un compte avec cet email existe déjà.'}, 400
        user = User(username=username, email=email)
        user.set_password(password)
        user.save()
        return {'message': 'Utilisateur créé avec succès'}, 201

    def authenticate_user(self, identifier: str, password: str) -> Tuple[Dict[str, Any], int]:
        """
        Authentifie un utilisateur et génère des tokens JWT.
        """
        user = User.find_by_identifier(identifier)
        if not user or not user.check_password(password):
            return {'errors': 'Identifiants incorrects.'}, 401
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))

        # Décoder les tokens pour obtenir le jti
        decoded_access_token = decode_token(access_token)
        decoded_refresh_token = decode_token(refresh_token)
        access_jti = decoded_access_token['jti']
        refresh_jti = decoded_refresh_token['jti']

        # Stocker les jti dans Redis sous une clé associée à l'utilisateur
        redis_client = current_app.redis_client
        if redis_client:
            user_token_key = f"user_tokens:{str(user.id)}"
            redis_client.sadd(user_token_key, access_jti, refresh_jti)

        return {'access_token': access_token, 'refresh_token': refresh_token}, 200

    def revoke_token(self, jti: str, token_type: str, exp: int, user_id: str) -> None:
        """
        Révoque un token JWT en le stockant dans Redis.
        """
        try:
            expires_in_seconds = exp - int(datetime.utcnow().timestamp())
            redis_client = current_app.redis_client
            if redis_client:
                # Marquer le token comme révoqué
                redis_client.set(jti, 'true', ex=expires_in_seconds)
                # Retirer le jti de l'ensemble des tokens de l'utilisateur
                user_token_key = f"user_tokens:{user_id}"
                redis_client.srem(user_token_key, jti)
        except Exception as e:
            logging.error(f'Erreur lors de la révocation du token: {e}')

    def revoke_all_tokens(self, user_id: str) -> None:
        """
        Révoque tous les tokens associés à un utilisateur.
        """
        redis_client = current_app.redis_client
        if redis_client:
            user_token_key = f"user_tokens:{user_id}"
            jtis = redis_client.smembers(user_token_key)
            for jti in jtis:
                # Marquer chaque token comme révoqué
                redis_client.set(jti, 'true', ex=3600)  # Définir une expiration appropriée
            # Supprimer l'ensemble des tokens de l'utilisateur
            redis_client.delete(user_token_key)

    def request_password_reset(self, email: str) -> Tuple[Dict[str, Any], int]:
        """
        Génère un token de réinitialisation et envoie un email à l'utilisateur.
        """
        user = User.objects(email=email).first()
        if user:
            token = self.generate_password_reset_token(email)
            self.send_password_reset_email(email, token)
        return {'message': 'Si un compte avec cet email existe, un email de réinitialisation a été envoyé.'}, 200

    def generate_password_reset_token(self, identifier: str) -> str:
        """
        Génère un token sécurisé pour la réinitialisation du mot de passe.
        """
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return serializer.dumps(identifier, salt='password-reset-salt')

    def send_password_reset_email(self, email: str, token: str) -> None:
        """
        Envoie un email de réinitialisation de mot de passe à l'utilisateur.
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
            # Envoi asynchrone de l'email
            Thread(target=mail.send, args=(msg,)).start()
            logging.info(f'Email de réinitialisation envoyé à {email}')
        except Exception as e:
            logging.error(f'Erreur lors de l\'envoi de l\'email de réinitialisation: {e}')

    def verify_password_reset_token(self, token: str, expiration: int = 3600) -> Optional[str]:
        """
        Vérifie la validité du token de réinitialisation.
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
        """
        email = self.verify_password_reset_token(token)
        if not email:
            return {'errors': 'Token invalide ou expiré.'}, 400
        user = User.objects(email=email).first()
        if not user:
            return {'errors': 'Utilisateur non trouvé.'}, 400
        try:
            # Validation du nouveau mot de passe
            password_field = ResetPasswordSchema().fields['password']
            password_field.validate(new_password)
        except ValidationError as err:
            return {'errors': err.messages}, 400
        user.set_password(new_password)
        user.save()
        self.revoke_all_tokens(str(user.id))
        return {'message': 'Mot de passe réinitialisé avec succès.'}, 200

    def generate_one_time_code(self) -> str:
        """
        Génère un code à usage unique de 6 chiffres.
        """
        return f"{random.randint(100000, 999999)}"

    def request_one_time_code(self, email: str) -> Tuple[Dict[str, Any], int]:
        """
        Génère un code à usage unique, le stocke dans Redis et envoie un email à l'utilisateur.
        """
        user = User.objects(email=email).first()
        if not user:
            return {'errors': 'Utilisateur non trouvé.'}, 404

        code = self.generate_one_time_code()
        redis_client = current_app.redis_client
        if redis_client:
            # Stocker le code dans Redis avec une durée de validité
            expires_in_seconds = current_app.config.get('ONE_TIME_CODE_EXPIRATION', 600)
            redis_client.set(f"one_time_code:{email}", code, ex=expires_in_seconds)
        else:
            current_app.logger.error("Redis client non disponible.")
            return {'errors': 'Service temporairement indisponible.'}, 503

        self.send_one_time_code_email(email, code)
        return {'message': 'Un code à usage unique a été envoyé à votre adresse email.'}, 200

    def send_one_time_code_email(self, email: str, code: str) -> None:
        """
        Envoie le code à usage unique par email à l'utilisateur.
        """
        try:
            msg = Message(
                subject="Votre code à usage unique",
                sender=current_app.config['MAIL_DEFAULT_SENDER'],
                recipients=[email]
            )
            msg.body = (
                f"Votre code à usage unique est : {code}\n\n"
                "Ce code est valable pendant 10 minutes."
            )
            # Envoi asynchrone de l'email
            Thread(target=mail.send, args=(msg,)).start()
            logging.info(f'One-time code envoyé à {email}')
        except Exception as e:
            logging.error(f'Erreur lors de l\'envoi du one-time code: {e}')

    def verify_one_time_code(self, email: str, code: str) -> Tuple[Dict[str, Any], int]:
        """
        Vérifie le code à usage unique fourni par l'utilisateur.
        """
        redis_client = current_app.redis_client
        if not redis_client:
            current_app.logger.error("Redis client non disponible.")
            return {'errors': 'Service temporairement indisponible.'}, 503

        stored_code = redis_client.get(f"one_time_code:{email}")
        if not stored_code:
            return {'errors': 'Code invalide ou expiré.'}, 400

        if stored_code != code:
            return {'errors': 'Code incorrect.'}, 400

        # Optionnel : Révoquer le code après utilisation
        redis_client.delete(f"one_time_code:{email}")

        # Générer un token d'accès pour l'utilisateur
        user = User.objects(email=email).first()
        if not user:
            return {'errors': 'Utilisateur non trouvé.'}, 400

        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))

        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'message': 'Authentification réussie.'
        }, 200
