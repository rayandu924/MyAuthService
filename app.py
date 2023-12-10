from flask import Flask, jsonify
import mysql.connector

app = Flask(__name__)

# MySQL Configuration
mysql_config = {
    'host': 'healer-database', # Nom du conteneur MySQL
    'user': 'healer',
    'password': 'healer',
    'database': 'healer'
}

# Create a MySQL connection
conn = mysql.connector.connect(host=mysql_config['host'],
                               user=mysql_config['user'],
                               password=mysql_config['password'],
                               database=mysql_config['database'])

@app.route('/')
def index():
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM user")
        results = cursor.fetchall()
        cursor.close()
        
        return jsonify(results)
    except Exception as e:
        return str(e)

if __name__ == '__main__':
    app.run(debug=True)
