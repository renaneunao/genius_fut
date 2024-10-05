import mysql.connector

def criar_tabelas(controller):
    print(f'Logged_In Criar Tabelas: {controller.get('logged_in')}')
    print(f'Cliente Criar Tabelas: {controller.get('cliente_id')}')
    conn = mysql.connector.connect(
        host='geniusfut.c7k02g0my0as.us-east-2.rds.amazonaws.com',
        user='renaneunao',
        password='*Vitorya111',
        database='geniusfut_database',
        port=3306
    )
    cursor = conn.cursor()

    # Create table for credentials
    cursor.execute('''CREATE TABLE IF NOT EXISTS credenciais (
        id INT AUTO_INCREMENT PRIMARY KEY,
        usuario VARCHAR(255) UNIQUE,
        senha VARCHAR(255)
    )''')

    # Create table for clients with detailed address fields
    cursor.execute('''CREATE TABLE IF NOT EXISTS clientes (
        id INT AUTO_INCREMENT PRIMARY KEY,
        usuario VARCHAR(255) UNIQUE,
        nome VARCHAR(255),
        telefone VARCHAR(20) UNIQUE,
        data_nascimento DATE,
        pais VARCHAR(255),
    )''')

    # Create table for client access
    cursor.execute('''CREATE TABLE IF NOT EXISTS acesso_cliente (
        cliente_id INT,
        data_limite DATE,
        bypass INT,
        FOREIGN KEY (cliente_id) REFERENCES clientes (id) ON DELETE CASCADE
    )''')

    # Commit the changes to the database
    conn.commit()
    cursor.close()
    conn.close()