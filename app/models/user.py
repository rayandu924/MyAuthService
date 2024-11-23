# app/models/user.py

from app.extensions import db, bcrypt
from mongoengine import Q

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
    password_hash = db.StringField(required=True)

    def set_password(self, password: str) -> None:
        """
        Hash le mot de passe et le stocke dans password_hash.

        :param password: Le mot de passe en clair.
        """
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password: str) -> bool:
        """
        Vérifie si le mot de passe fourni correspond au hachage stocké.

        :param password: Le mot de passe en clair.
        :return: True si le mot de passe est correct, False sinon.
        """
        return bcrypt.check_password_hash(self.password_hash, password)

    @staticmethod
    def find_by_identifier(identifier: str):
        """
        Trouve un utilisateur par nom d'utilisateur ou email.

        :param identifier: Le nom d'utilisateur ou l'email.
        :return: Un objet User ou None.
        """
        return User.objects(Q(username=identifier) | Q(email=identifier)).first()
