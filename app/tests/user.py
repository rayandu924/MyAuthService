# app/tests/user.py

import unittest
from app import create_app
from app.extensions import db
from app.config import TestingConfig
from unittest.mock import patch
from flask_jwt_extended import decode_token

class UserTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(config_class=TestingConfig)
        self.client = self.app.test_client()
        with self.app.app_context():
            # Configuration pour une base de données de test
            db.connection.drop_database('testdb')

    def test_register_user(self):
        with self.app.app_context():
            response = self.client.post('/user/register', json={
                'username': 'testuser',
                'email': 'test@example.com',
                'password': 'Test1234@'
            })
            self.assertEqual(response.status_code, 201)
            data = response.get_json()
            self.assertIn('message', data)
            self.assertEqual(data['message'], 'Utilisateur créé avec succès')

    def test_register_existing_user(self):
        with self.app.app_context():
            # Enregistre d'abord l'utilisateur
            self.client.post('/user/register', json={
                'username': 'testuser',
                'email': 'test@example.com',
                'password': 'Test1234@'
            })
            # Tente de réenregistrer le même utilisateur
            response = self.client.post('/user/register', json={
                'username': 'testuser',
                'email': 'test@example.com',
                'password': 'Test1234@'
            })
            self.assertEqual(response.status_code, 400)
            data = response.get_json()
            self.assertIn('errors', data)

    def test_login_user(self):
        with self.app.app_context():
            # Enregistre d'abord l'utilisateur
            self.client.post('/user/register', json={
                'username': 'testuser',
                'email': 'test@example.com',
                'password': 'Test1234@'
            })
            # Puis tente de se connecter
            response = self.client.post('/user/login', json={
                'identifier': 'testuser',
                'password': 'Test1234@'
            })
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertIn('access_token', data)
            self.assertIn('refresh_token', data)

    def test_login_invalid_credentials(self):
        with self.app.app_context():
            # Tente de se connecter sans enregistrer
            response = self.client.post('/user/login', json={
                'identifier': 'nonexistent',
                'password': 'WrongPass123@'
            })
            self.assertEqual(response.status_code, 401)
            data = response.get_json()
            self.assertIn('errors', data)

    @patch('app.services.user.UserService.send_password_reset_email')
    def test_password_reset_request(self, mock_send_email):
        with self.app.app_context():
            # Enregistre l'utilisateur
            self.client.post('/user/register', json={
                'username': 'testuser',
                'email': 'test@example.com',
                'password': 'Test1234@'
            })
            # Demande de réinitialisation de mot de passe
            response = self.client.post('/user/request_password_reset', json={
                'email': 'test@example.com'
            })
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertIn('message', data)
            self.assertEqual(data['message'], 'Si un compte avec cet email existe, un email de réinitialisation a été envoyé.')
            mock_send_email.assert_called_once()

    def test_password_reset_invalid_token(self):
        with self.app.app_context():
            # Tente de réinitialiser le mot de passe avec un token invalide
            response = self.client.post('/user/reset_password', json={
                'token': 'invalidtoken',
                'password': 'NewPass123@'
            })
            self.assertEqual(response.status_code, 400)
            data = response.get_json()
            self.assertIn('errors', data)

    def tearDown(self):
        with self.app.app_context():
            db.connection.drop_database('testdb')

if __name__ == '__main__':
    unittest.main()
