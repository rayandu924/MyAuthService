#Liste des technologies de l'application à implémenter
# x JSON Web Token (JWT), Cette technologie permet de sécuriser les échanges entre le client et le serveur
# x Limiter (Flask-Limiter), Cette technologie permet de limiter le nombre de requêtes
# x SQLAlchemy, Cette technologie permet de gérer la base de données
# Eviter de gerer les objets JSON au début des endpoints c chiant pour l'instant et peux modulable, utiliser le principe de sqlalchemy pour filtrer sur les champs qui ont des conlonne pour la table

#Importation des modules
from flask import Flask # module pour créer une application Flask
from flask import render_template # module pour gérer les templates HTML
from flask import jsonify # module pour convertir un objet Python en JSON
from flask import request # module pour obtenir des données à partir d'une requête HTTP
from flask_limiter import Limiter # module pour limiter le nombre de requêtes
from flask_limiter.util import get_remote_address # module pour obtenir l'adresse IP de l'utilisateur
from flask_jwt_extended import JWTManager # module pour gérer les tokens JWT
from flask_jwt_extended import create_access_token # module pour créer un access token
from flask_jwt_extended import create_refresh_token # module pour créer un refresh token
from flask_jwt_extended import jwt_required # module pour protéger les routes
from flask_jwt_extended import get_jwt_identity # module pour obtenir l'identité de l'utilisateur courant
from flask_jwt_extended import get_jwt # module pour obtenir les claims de l'utilisateur courant
from flask_sqlalchemy import SQLAlchemy # module pour gérer la base de données
from flask_socketio import SocketIO # module pour gérer les websockets
from flask_socketio import send # module pour envoyer un message à tous les clients connectés
from datetime import timedelta # module pour gérer les durées

# ********** Initialisation de l'application **********

# Création de l'application Flask
app = Flask(__name__) # création de l'application Flask

# Configuration de l'application Flask

# ********** Initialisation des extensions **********

# Initialisation de l'extension Limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["10 per minute"]
)

# Configuration de l'extension JWT
app.config['JWT_SECRET_KEY'] = '667hannnnnnnnnnekip' # configuration de la clé secrète pour générer et vérifier les tokens
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1) # configuration de la durée de validité de l'access token
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30) # configuration de la durée de validité du refresh token

# Initialisation de l'extension JWT
jwt = JWTManager(app) # initialisation de l'extension JWT

# Configuration de l'extension SocketIO

# Initialisation de l'extension SocketIO
socketio = SocketIO(app) # initialisation de l'extension SocketIO

# Configuration de l'extension SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://healer:healer@localhost:3306/healer' # configuration de l'URI de la base de données

# Initialisation de l'extension SQLAlchemy
db = SQLAlchemy(app) # initialisation de l'extension SQLAlchemy

# ********** Définition des modèles **********
class Utilisateur(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    
# ********** Création des tables **********
with app.app_context():
    db.create_all()

# ********** Fonctions **********

# ********** Routes **********

# Route pour obtenir un access token et un refresh token à l'aide d'un nom d'utilisateur et d'un mot de passe
@app.route('/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    # Récupérez les données de la requête
    data = request.get_json()
    
    # Verifiez si le nom d'utilisateur et le mot de passe sont corrects, si ce n'est pas le cas, retournez une erreur
    if data['username'] != 'admin' or data['password'] != 'admin':
        return jsonify({'error': 'invalid_credentials'}), 401

    # Créez les tokens 
    access_token = create_access_token(identity=data['username'], fresh=True, additional_claims={'role': 'admin'})
    refresh_token = create_refresh_token(identity=data['username'], additional_claims={'role': 'admin'})
    
    return jsonify(access_token=access_token, refresh_token=refresh_token)

@app.route('/protected', methods=['GET']) # Route protégée, accessible uniquement avec un access token valide
@jwt_required() # l'access token dans le header Authorization est requis pour accéder à cette route
def protected():
    current_user = get_jwt_identity()
    current_user_claims = get_jwt()
    return jsonify(logged_in_as=current_user, role=current_user_claims['role']), 200

@app.route('/token/refresh', methods=['POST']) # Route pour obtenir un nouveau access token à l'aide d'un refresh token
@jwt_required(refresh=True) # le refresh token dans le header Authorization est requis pour accéder à cette route
def refresh():
    current_user = get_jwt_identity()
    current_user_claims = get_jwt()
    print(current_user_claims)
    print(current_user)
    new_access_token = create_access_token(identity=current_user, fresh=True, additional_claims={'role': current_user_claims['role']})
    new_refresh_token = create_refresh_token(identity=current_user, additional_claims={'role': current_user_claims['role']})
    return jsonify(access_token=new_access_token, refresh_token=new_refresh_token), 200

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('message')
def handle_message(message):
    print('received message: ' + message)
    send(message, broadcast=True)

if __name__ == '__main__':
    app.run(debug=True)

# fonction pour retourner une erreur si le nombre de requêtes est dépassé
@limiter.error_handler
def ratelimit_handler(e):
    return "Trop de requêtes !", 429
