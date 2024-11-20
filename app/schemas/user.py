# app/schemas/user.py

from marshmallow import Schema, fields, validate


class RegisterSchema(Schema):
    username = fields.Str(
        required=True,
        validate=[
            validate.Length(min=3, max=50, error='Le nom d\'utilisateur doit contenir entre 3 et 50 caractères.'),
            validate.Regexp('^[a-zA-Z0-9_]+$', error='Le nom d\'utilisateur ne peut contenir que des lettres, des chiffres et des underscores.')
        ]
    )
    email = fields.Email(required=True)
    password = fields.Str(
        required=True,
        load_only=True,
        validate=[
            validate.Length(min=8),
            validate.Regexp(
                '^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&]).{8,}$',
                error='Le mot de passe doit contenir au moins 8 caractères, dont des lettres, des chiffres et des caractères spéciaux.'
            )
        ]
    )


class LoginSchema(Schema):
    username = fields.Str(required=True)
    password = fields.Str(required=True, load_only=True)


class RequestPasswordResetSchema(Schema):
    email = fields.Email(required=True)


class ResetPasswordSchema(Schema):
    token = fields.Str(required=True)
    password = fields.Str(
        required=True,
        load_only=True,
        validate=[
            validate.Length(min=8),
            validate.Regexp(
                '^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&]).{8,}$',
                error='Le mot de passe doit contenir au moins 8 caractères, dont des lettres, des chiffres et des caractères spéciaux.'
            )
        ]
    )
