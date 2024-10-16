import mysql.connector
from UTILS.connection import get_connection

def criar_tabelas():
    # Conectar ao banco de dados
    conn = get_connection()
    cursor = conn.cursor()

    # Criar a nova database geniusfut_database
    cursor.execute("CREATE DATABASE IF NOT EXISTS geniusfut_database")

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
        pais VARCHAR(255)
    )''')

    # Criar tabela de acessos de clientes
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS acesso_cliente (
                cliente_id INT,
                bypass INT,
                trial_credits BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (cliente_id) REFERENCES clientes (id) ON DELETE CASCADE
            )
        ''')

    # Criar tabela de consumos
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS consumos (
                id INT AUTO_INCREMENT PRIMARY KEY,
                cliente_id INT,
                datahora DATETIME,
                valor_consumo DECIMAL(10, 2),
                configuracao_consumo VARCHAR(255),
                FOREIGN KEY (cliente_id) REFERENCES clientes (id) ON DELETE CASCADE
            )
        ''')

    # Criar tabela de compras de créditos
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS compras_creditos (
                id INT AUTO_INCREMENT PRIMARY KEY,
                cliente_id INT,
                datahora DATETIME,
                valor_compra DECIMAL(10, 2),
                FOREIGN KEY (cliente_id) REFERENCES clientes (id) ON DELETE CASCADE
            )
        ''')

    # Commit the changes to the database
    conn.commit()
    cursor.close()
    conn.close()

criar_tabelas()

