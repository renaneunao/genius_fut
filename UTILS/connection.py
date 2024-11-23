import mysql.connector


def get_connection():
    # Conectar ao MySQL
    connection = mysql.connector.connect(
        host='geniusfut.mysql.uhserver.com',
        user='renaneunao',
        password='*Vitorya122',
        database='geniusfut',
        port=3306
    )
    return connection

