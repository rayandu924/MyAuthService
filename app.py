from flask import Flask, jsonify
import mysql.connector

app = Flask(__name__)

# MySQL Configuration
mysql_config = {
    'host': 'localhost', # Replace with your MySQL host IP address
    'user': 'user',     # Replace with your MySQL username
    'password': 'password', # Replace with your MySQL password
    'database': 'healer'        # Replace with your MySQL database name
}

# Create a MySQL connection
conn = mysql.connector.connect(host=mysql_config['host'],
                               user=mysql_config['user'],
                               password=mysql_config['password'],
                               database=mysql_config['database'])

@app.route('/')
def index():

if __name__ == '__main__':
    app.run(debug=True)
