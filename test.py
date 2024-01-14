import unittest
import requests

# Configuration de la test suite
base_url = 'http://localhost:5000'
login_url = base_url + '/login'

# Classe de test
class Test(unittest.TestCase):

    # Test de connexion avec des identifiants valides
    def test_valid_credentials(self):
        response = requests.post(login_url, json={'username': 'admin', 'password': 'admin'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue('access_token' in response.json())
        self.assertTrue('refresh_token' in response.json())

    # Test de connexion avec des identifiants invalides
    def test_invalid_credentials(self):
        response = requests.post(login_url, json={'username': 'admin', 'password': 'wrong_password'})
        self.assertEqual(response.status_code, 401)
        self.assertTrue('access_token' not in response.json())
        self.assertTrue('refresh_token' not in response.json())
        
    # Test de connexion avec des identifiants valides puis récupération d'une ressource protégée avec l'access token
    def test_protected_resource(self):
        response = requests.post(login_url, json={'username': 'admin', 'password': 'admin'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue('access_token' in response.json())
        self.assertTrue('refresh_token' in response.json())
        
        access_token = response.json()['access_token']
        response = requests.get(base_url + '/protected', headers={'Authorization': 'Bearer ' + access_token})
        self.assertEqual(response.status_code, 200)
        self.assertTrue('logged_in_as' in response.json())
        self.assertTrue('role' in response.json())
        self.assertEqual(response.json()['logged_in_as'], 'admin')
        self.assertEqual(response.json()['role'], 'admin')
        
    # Test de connexion avec des identifiants valides puis récupération d'une ressource protégée avec l'access token invalide
    def test_protected_resource_with_invalid_access_token(self):        
        access_token = 'wrong_access_token'
        response = requests.get(base_url + '/protected', headers={'Authorization': 'Bearer ' + access_token})
        self.assertEqual(response.status_code, 422)
        self.assertTrue('logged_in_as' not in response.json())
        self.assertTrue('role' not in response.json())      

    # Test de connexion avec des identifiants valides puis récupération d'un nouveau access token à l'aide du refresh token
    def test_refresh_token(self):
        response = requests.post(login_url, json={'username': 'admin', 'password': 'admin'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue('access_token' in response.json())
        self.assertTrue('refresh_token' in response.json())
        
        refresh_token = response.json()['refresh_token']
        response = requests.post(base_url + '/token/refresh', headers={'Authorization': 'Bearer ' + refresh_token})
        self.assertEqual(response.status_code, 200)
        self.assertTrue('access_token' in response.json())
        self.assertTrue('refresh_token' in response.json())
        
        access_token = response.json()['access_token']
        refresh_token = response.json()['refresh_token']
        response = requests.get(base_url + '/protected', headers={'Authorization': 'Bearer ' + access_token})
        print(response.json())
        self.assertEqual(response.status_code, 200)
        self.assertTrue('logged_in_as' in response.json())
        self.assertTrue('role' in response.json())
        self.assertEqual(response.json()['logged_in_as'], 'admin')
        self.assertEqual(response.json()['role'], 'admin')

# Exécuter les tests si le script est exécuté directement
if __name__ == '__main__':
    unittest.main()
