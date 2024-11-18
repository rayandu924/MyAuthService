# app/controllers/user.py

from flask import Blueprint, request
from app.services.user import UserService
from app.schemas.user import UserSchema
from marshmallow import ValidationError
from app.extensions import limiter
from flask_jwt_extended import (
    jwt_required,
    get_jwt,
    get_jwt_identity,
    create_access_token,
)

user_bp = Blueprint('user_bp', __name__)
user_service = UserService()

@user_bp.route('/register', methods=['POST'])
@limiter.limit("5 per minute")
def register():
    json_data = request.get_json()
    try:
        data = UserSchema().load(json_data)
    except ValidationError as err:
        return {'errors': err.messages}, 400
    username = data['username']
    email = data['email']
    password = data['password']
    return user_service.register_user(username, email, password)

@user_bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    json_data = request.get_json()
    try:
        data = UserSchema().load(json_data , partial=('email',))
    except ValidationError as err:
        return {'errors': err.messages}, 400
    username = data['username']
    password = data['password']
    return user_service.authenticate_user(username, password)

@user_bp.route('/request_password_reset', methods=['POST'])
@limiter.limit("5 per minute")
def request_password_reset():
    json_data = request.get_json()
    try:
        data = UserSchema().load(json_data , partial=('username', 'password',))
    except ValidationError as err:
        return {'errors': err.messages}, 400
    email = data['email']
    return user_service.request_password_reset(email)

@user_bp.route('/reset_password', methods=['POST'])
def reset_password():
    json_data = request.get_json()
    try:
        data = UserSchema().load(json_data.setdefault('token', None) , partial=('username', 'email',)) # setdefault to avoid make one more test, waiting marshmallow upgrade to make some fields unrequired
    except ValidationError as err:
        return {'errors': err.messages}, 400
    token = data.get('token')
    new_password = data.get('password')
    return user_service.reset_password(token, new_password)

@user_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user = get_jwt_identity()
    new_access_token = create_access_token(identity=current_user)
    return {'access_token': new_access_token}, 200

@user_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    jti = get_jwt()['jti']
    user_service.revoke_token(jti)
    return {'message': 'Déconnexion réussie.'}, 200