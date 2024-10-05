import mysql.connector


def get_connection():
    connection = mysql.connector.connect(
            host='geniusfut.c7k02g0my0as.us-east-2.rds.amazonaws.com',
            user='renaneunao',
            password='*Vitorya111',
            database='geniusfut_database',
            port=3306
        )
    return connection
