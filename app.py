from flask import Flask
import mysql.connector

app = Flask(__name__)

# Configuration de la base de données
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'votre_utilisateur'
app.config['MYSQL_PASSWORD'] = 'votre_mot_de_passe'
app.config['MYSQL_DB'] = 'nom_de_la_base_de_donnees'

# Initialiser la connexion à la base de données
db = mysql.connector.connect(
    host=app.config['MYSQL_HOST'],
    user=app.config['MYSQL_USER'],
    password=app.config['MYSQL_PASSWORD'],
    database=app.config['MYSQL_DB']
)

@app.route('/')
def index():
    return "Bienvenue sur mon serveur Flask connecté à MySQL!"

@app.route('/data')
def data():
    cursor = db.cursor()
    cursor.execute("SELECT * FROM votre_table")
    data = cursor.fetchall()
    cursor.close()
    return str(data)

if __name__ == '__main__':
    app.run(debug=True)
