# app/models/user.py

from app.extensions import db, bcrypt
from datetime import datetime
from typing import Any

class User(db.Document):
    """
    Modèle représentant un utilisateur.
    """
    meta = {
        'collection': 'users',
        'indexes': [
            {'fields': ['username'], 'unique': True},
            {'fields': ['email'], 'unique': True}
        ],
        'strict': True
    }
    username = db.StringField(required=True, unique=True, max_length=50)
    email = db.EmailField(required=True, unique=True)
    password_hash = db.StringField(required=True, max_length=128)

    def set_password(self, password: str) -> None:
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password: str) -> bool:
        return bcrypt.check_password_hash(self.password_hash, password)
