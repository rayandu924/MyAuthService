# app/controllers/user.py

from flask import Blueprint, request
from app.services.user import UserService
from app.schemas.user import (
    RegisterSchema,
    LoginSchema,
    RequestPasswordResetSchema,
    ResetPasswordSchema
)
from marshmallow import ValidationError
from app.extensions import limiter
from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity,
    create_access_token
)

user_bp = Blueprint('user_bp', __name__)
user_service = UserService()

@user_bp.route('/register', methods=['POST'])
@limiter.limit("5 per minute")
def register():
    """
    Endpoint pour l'enregistrement d'un nouvel utilisateur.
    """
    json_data = request.get_json()
    try:
        data = RegisterSchema().load(json_data)
    except ValidationError as err:
        return {'errors': err.messages}, 400
    username = data['username']
    email = data['email']
    password = data['password']
    return user_service.register_user(username, email, password)

@user_bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    """
    Endpoint pour l'authentification d'un utilisateur.
    """
    json_data = request.get_json()
    try:
        data = LoginSchema().load(json_data)
    except ValidationError as err:
        return {'errors': err.messages}, 400
    identifier = data['identifier']
    password = data['password']
    return user_service.authenticate_user(identifier, password)

@user_bp.route('/request_password_reset', methods=['POST'])
@limiter.limit("5 per minute")
def request_password_reset():
    """
    Endpoint pour demander une réinitialisation de mot de passe.
    """
    json_data = request.get_json()
    try:
        data = RequestPasswordResetSchema().load(json_data)
    except ValidationError as err:
        return {'errors': err.messages}, 400
    email = data['email']
    return user_service.request_password_reset(email)

@user_bp.route('/reset_password', methods=['POST'])
@limiter.limit("5 per minute")
def reset_password():
    """
    Endpoint pour réinitialiser le mot de passe avec le token fourni.
    """
    json_data = request.get_json()
    try:
        data = ResetPasswordSchema().load(json_data)
    except ValidationError as err:
        return {'errors': err.messages}, 400
    token = data['token']
    new_password = data['password']
    return user_service.reset_password(token, new_password)

@user_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
@limiter.limit("5 per minute")
def refresh():
    """
    Endpoint pour rafraîchir le token d'accès.
    """
    current_user = get_jwt_identity()
    new_access_token = create_access_token(identity=current_user)
    return {'access_token': new_access_token}, 200

@user_bp.route('/logout', methods=['POST'])
@jwt_required()
@limiter.limit("5 per minute")
def logout():
    """
    Endpoint pour la déconnexion de l'utilisateur.
    Révoque le token d'accès courant.
    """
    jti = get_jwt_identity()
    user_service.revoke_token(jti)
    return {'message': 'Déconnexion réussie.'}, 200
