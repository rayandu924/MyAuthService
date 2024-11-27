# app/tests/user.py

import unittest
from unittest.mock import patch
from app import create_app
from app.models.user import User
from mongoengine import disconnect
import json
from app.config import TestingConfig
from app.services.user import UserService
from app.extensions import limiter  # Import du limiter pour le reset

class UserTestCase(unittest.TestCase):
    def setUp(self):
        """
        Configuration exécutée avant chaque test.
        """
        # Création de l'application avec la configuration de test
        self.app = create_app(TestingConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

        # Initialisation du service utilisateur
        self.user_service = UserService()

        # Connexion à une base de données MongoDB de test
        with self.app.app_context():
            User.drop_collection()  # Assurez-vous que la collection est vide avant chaque test

        # Mock send_async_email pour éviter l'erreur de contexte d'application
        patcher = patch('app.services.user.UserService.send_async_email')
        self.mock_send_async_email = patcher.start()
        self.addCleanup(patcher.stop)

        # Réinitialiser le rate limiting pour chaque test
        limiter.reset()

    def tearDown(self):
        """
        Nettoyage exécuté après chaque test.
        """
        with self.app.app_context():
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
        data = json.loads(response.data)
        self.assertEqual(data.get('message'), 'Utilisateur créé avec succès')
        self.mock_send_async_email.assert_not_called()  # Pas d'email envoyé lors de l'enregistrement

    def test_register_user_existing_username(self):
        """
        Teste l'enregistrement avec un nom d'utilisateur déjà existant.
        """
        # Crée un utilisateur initial avec un mot de passe valide
        user = User(username='testuser', email='testuser1@example.com')
        user.set_password('Password123!')
        user.save()

        response = self.client.post('/user/register', json={
            'username': 'testuser',
            'email': 'testuser2@example.com',
            'password': 'Password123!'
        })
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('Le nom d\'utilisateur est déjà pris.', data.get('errors', ''))
        self.mock_send_async_email.assert_not_called()

    def test_register_user_existing_email(self):
        """
        Teste l'enregistrement avec un email déjà existant.
        """
        # Crée un utilisateur initial avec un mot de passe valide
        user = User(username='testuser1', email='testuser@example.com')
        user.set_password('Password123!')
        user.save()

        response = self.client.post('/user/register', json={
            'username': 'testuser2',
            'email': 'testuser@example.com',
            'password': 'Password123!'
        })
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('Un compte avec cet email existe déjà.', data.get('errors', ''))
        self.mock_send_async_email.assert_not_called()

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
        self.mock_send_async_email.assert_not_called()

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
        data = json.loads(response.data)
        self.assertIn('Identifiants incorrects.', data.get('errors', ''))
        self.mock_send_async_email.assert_not_called()

    def test_login_nonexistent_user(self):
        """
        Teste la connexion avec un utilisateur qui n'existe pas.
        """
        response = self.client.post('/user/login', json={
            'identifier': 'nonexistent',
            'password': 'Password123!'
        })
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertIn('Identifiants incorrects.', data.get('errors', ''))
        self.mock_send_async_email.assert_not_called()

    def test_request_password_reset(self):
        """
        Teste la demande de réinitialisation de mot de passe.
        """
        # Crée un utilisateur initial avec un mot de passe valide
        user = User(username='testuser', email='testuser@example.com')
        user.set_password('Password123!')
        user.save()

        response = self.client.post('/user/request_password_reset', json={
            'email': 'testuser@example.com'
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('message', data)
        self.assertEqual(data['message'], 'Si un compte avec cet email existe, un email de réinitialisation a été envoyé.')
        self.mock_send_async_email.assert_called_once()

    def test_reset_password_success(self):
        """
        Teste la réinitialisation réussie du mot de passe avec un token valide.
        """
        user = User(username='testuser', email='testuser@example.com')
        user.set_password('OldPassword123!')
        user.save()

        # Génère un token de réinitialisation valide
        token = self.user_service.generate_password_reset_token('testuser@example.com')

        response = self.client.post('/user/reset_password', json={
            'token': token,
            'password': 'NewPassword123!'
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data.get('message'), 'Mot de passe réinitialisé avec succès.')
        self.mock_send_async_email.assert_not_called()

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
        data = json.loads(response.data)
        self.assertIn('Token invalide ou expiré.', data.get('errors', ''))
        self.mock_send_async_email.assert_not_called()

    def test_request_one_time_code(self):
        """
        Teste la demande d'un code à usage unique.
        """
        # Crée un utilisateur initial avec un mot de passe valide
        user = User(username='testuser', email='testuser@example.com')
        user.set_password('Password123!')
        user.save()

        response = self.client.post('/user/request_one_time_code', json={
            'email': 'testuser@example.com'
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('message', data)
        self.assertEqual(data['message'], 'Un code à usage unique a été envoyé à votre adresse email.')
        self.mock_send_async_email.assert_called_once()

    def test_verify_one_time_code_success(self):
        """
        Teste la vérification réussie du code à usage unique.
        """
        # Crée un utilisateur initial avec un mot de passe valide
        user = User(username='testuser', email='testuser@example.com')
        user.set_password('Password123!')
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
        self.assertEqual(data.get('message'), 'Authentification réussie.')

    def test_verify_one_time_code_invalid(self):
        """
        Teste la vérification avec un code invalide.
        """
        # Crée un utilisateur initial avec un mot de passe valide
        user = User(username='testuser', email='testuser@example.com')
        user.set_password('Password123!')
        user.save()

        response = self.client.post('/user/verify_one_time_code', json={
            'email': 'testuser@example.com',
            'code': '654321'
        })
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        # Accepter les deux messages possibles
        self.assertTrue(
            'Code invalide ou expiré.' in data.get('errors', '') or
            'Code incorrect.' in data.get('errors', ''),
            "Expected either 'Code invalide ou expiré.' or 'Code incorrect.' in errors."
        )

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
        access_token = data.get('access_token')

        # Déconnexion
        response = self.client.post('/user/logout', headers={
            'Authorization': f'Bearer {access_token}'
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data.get('message'), 'Déconnexion réussie.')

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
        self.assertEqual(response.status_code, 200)  # Vérifier que la connexion est réussie
        data = json.loads(response.data)
        refresh_token = data.get('refresh_token')
        self.assertIsNotNone(refresh_token, "Refresh token should be present in the response.")

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
        data = json.loads(response.data)
        self.assertIn('msg', data)
        self.assertEqual(data['msg'], 'Missing Authorization Header')

    def test_rate_limiting(self):
        """
        Teste le rate limiting sur une route spécifique.
        """
        # Crée un utilisateur initial avec un mot de passe valide
        user = User(username='testuser', email='testuser@example.com')
        user.set_password('Password123!')
        user.save()

        # Effectue 5 requêtes légitimes
        for _ in range(5):
            response = self.client.post('/user/login', json={
                'identifier': 'testuser',
                'password': 'Password123!'
            })
            self.assertEqual(response.status_code, 200)

        # 6ème requête devrait être limitée
        response = self.client.post('/user/login', json={
            'identifier': 'testuser',
            'password': 'Password123!'
        })
        self.assertEqual(response.status_code, 429)
        data = json.loads(response.data)
        self.assertIn('error', data)
        # Ajustement de l'assertion pour correspondre au message réel
        self.assertIn('5 per 1 minute', data['error'])

if __name__ == '__main__':
    unittest.main()
