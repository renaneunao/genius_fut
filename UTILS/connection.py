import mysql.connector


def get_connection():
    # Conectar ao MySQL
    connection = mysql.connector.connect(
        host='geniusfut-2.c5y0u2k8gygo.us-east-1.rds.amazonaws.com',
        user='renaneunao',
        password='*Vitorya333',
        database='geniusfut_database',
        port=3306
    )
    return connection
