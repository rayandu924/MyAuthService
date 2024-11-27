# app/tests/user.py

import unittest
from flask import current_app
from app import create_app
from app.models.user import User
from mongoengine import disconnect
from flask_jwt_extended import decode_token
import json

class UserTestCase(unittest.TestCase):
    def setUp(self):
        """
        Configuration exécutée avant chaque test.
        """
        # Configuration de l'application pour les tests
        self.app = create_app('app.config.TestingConfig')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

        # Connexion à une base de données MongoDB de test
        User.drop_collection()  # Assurez-vous que la collection est vide avant chaque test

    def tearDown(self):
        """
        Nettoyage exécuté après chaque test.
        """
        User.drop_collection()
        disconnect()
        self.app_context.pop()

    def test_register_user_success(self):
        """
        Teste l'enregistrement réussi d'un nouvel utilisateur.
        """
        response = self.client.post('/user/register', json={
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': 'Password123!'
        })
        self.assertEqual(response.status_code, 201)
        self.assertIn('Utilisateur créé avec succès', response.get_data(as_text=True))

    def test_register_user_existing_username(self):
        """
        Teste l'enregistrement avec un nom d'utilisateur déjà existant.
        """
        # Crée un utilisateur initial
        User(username='testuser', email='testuser1@example.com', password_hash='hashed').save()

        response = self.client.post('/user/register', json={
            'username': 'testuser',
            'email': 'testuser2@example.com',
            'password': 'Password123!'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('Le nom d\'utilisateur est déjà pris.', response.get_data(as_text=True))

    def test_register_user_existing_email(self):
        """
        Teste l'enregistrement avec un email déjà existant.
        """
        # Crée un utilisateur initial
        User(username='testuser1', email='testuser@example.com', password_hash='hashed').save()

        response = self.client.post('/user/register', json={
            'username': 'testuser2',
            'email': 'testuser@example.com',
            'password': 'Password123!'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('Un compte avec cet email existe déjà.', response.get_data(as_text=True))

    def test_login_success(self):
        """
        Teste la connexion réussie avec des identifiants valides.
        """
        # Crée un utilisateur initial
        user = User(username='testuser', email='testuser@example.com')
        user.set_password('Password123!')
        user.save()

        response = self.client.post('/user/login', json={
            'identifier': 'testuser',
            'password': 'Password123!'
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('access_token', data)
        self.assertIn('refresh_token', data)

    def test_login_invalid_password(self):
        """
        Teste la connexion avec un mot de passe invalide.
        """
        # Crée un utilisateur initial
        user = User(username='testuser', email='testuser@example.com')
        user.set_password('Password123!')
        user.save()

        response = self.client.post('/user/login', json={
            'identifier': 'testuser',
            'password': 'WrongPassword!'
        })
        self.assertEqual(response.status_code, 401)
        self.assertIn('Identifiants incorrects.', response.get_data(as_text=True))

    def test_login_nonexistent_user(self):
        """
        Teste la connexion avec un utilisateur qui n'existe pas.
        """
        response = self.client.post('/user/login', json={
            'identifier': 'nonexistent',
            'password': 'Password123!'
        })
        self.assertEqual(response.status_code, 401)
        self.assertIn('Identifiants incorrects.', response.get_data(as_text=True))

    def test_request_password_reset(self):
        """
        Teste la demande de réinitialisation de mot de passe.
        """
        # Crée un utilisateur initial
        user = User(username='testuser', email='testuser@example.com')
        user.save()

        response = self.client.post('/user/request_password_reset', json={
            'email': 'testuser@example.com'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('un email de réinitialisation a été envoyé', response.get_data(as_text=True))

    def test_reset_password_success(self):
        """
        Teste la réinitialisation réussie du mot de passe avec un token valide.
        """
        user = User(username='testuser', email='testuser@example.com')
        user.set_password('OldPassword123!')
        user.save()

        # Génère un token de réinitialisation valide
        token = self.app.user_service.generate_password_reset_token('testuser@example.com')

        response = self.client.post('/user/reset_password', json={
            'token': token,
            'password': 'NewPassword123!'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('Mot de passe réinitialisé avec succès.', response.get_data(as_text=True))

        # Vérifie que le mot de passe a été mis à jour
        updated_user = User.objects(username='testuser').first()
        self.assertTrue(updated_user.check_password('NewPassword123!'))

    def test_reset_password_invalid_token(self):
        """
        Teste la réinitialisation du mot de passe avec un token invalide.
        """
        response = self.client.post('/user/reset_password', json={
            'token': 'invalidtoken',
            'password': 'NewPassword123!'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('Token invalide ou expiré.', response.get_data(as_text=True))

    def test_request_one_time_code(self):
        """
        Teste la demande d'un code à usage unique.
        """
        user = User(username='testuser', email='testuser@example.com')
        user.save()

        response = self.client.post('/user/request_one_time_code', json={
            'email': 'testuser@example.com'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('Un code à usage unique a été envoyé', response.get_data(as_text=True))

    def test_verify_one_time_code_success(self):
        """
        Teste la vérification réussie du code à usage unique.
        """
        user = User(username='testuser', email='testuser@example.com')
        user.save()

        # Génère et stocke un code dans Redis
        code = '123456'
        self.app.redis_client.set(f'one_time_code:{user.email}', code, ex=600)

        response = self.client.post('/user/verify_one_time_code', json={
            'email': 'testuser@example.com',
            'code': '123456'
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('access_token', data)
        self.assertIn('refresh_token', data)
        self.assertIn('Authentification réussie.', data['message'])

    def test_verify_one_time_code_invalid(self):
        """
        Teste la vérification avec un code invalide.
        """
        user = User(username='testuser', email='testuser@example.com')
        user.save()

        response = self.client.post('/user/verify_one_time_code', json={
            'email': 'testuser@example.com',
            'code': '654321'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('Code invalide ou expiré.', response.get_data(as_text=True))

    def test_logout(self):
        """
        Teste la déconnexion de l'utilisateur.
        """
        # Crée un utilisateur et connecte-le
        user = User(username='testuser', email='testuser@example.com')
        user.set_password('Password123!')
        user.save()

        response = self.client.post('/user/login', json={
            'identifier': 'testuser',
            'password': 'Password123!'
        })
        data = json.loads(response.data)
        access_token = data['access_token']

        # Déconnexion
        response = self.client.post('/user/logout', headers={
            'Authorization': f'Bearer {access_token}'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('Déconnexion réussie.', response.get_data(as_text=True))

    def test_refresh_token(self):
        """
        Teste le rafraîchissement du token d'accès.
        """
        # Crée un utilisateur et connecte-le
        user = User(username='testuser', email='testuser@example.com')
        user.set_password('Password123!')
        user.save()

        response = self.client.post('/user/login', json={
            'identifier': 'testuser',
            'password': 'Password123!'
        })
        data = json.loads(response.data)
        refresh_token = data['refresh_token']

        # Rafraîchir le token
        response = self.client.post('/user/refresh', headers={
            'Authorization': f'Bearer {refresh_token}'
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('access_token', data)

    def test_access_protected_route_without_token(self):
        """
        Teste l'accès à une route protégée sans token.
        """
        response = self.client.post('/user/logout')
        self.assertEqual(response.status_code, 401)

    def test_rate_limiting(self):
        """
        Teste le rate limiting sur une route spécifique.
        """
        for _ in range(6):
            response = self.client.post('/user/login', json={
                'identifier': 'testuser',
                'password': 'Password123!'
            })
        self.assertEqual(response.status_code, 429)
        self.assertIn('Ratelimit exceeded', response.get_data(as_text=True))


if __name__ == '__main__':
    unittest.main()
