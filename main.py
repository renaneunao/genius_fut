import streamlit as st
import sqlite3
from streamlit_cookies_controller import CookieController
from login import login, criar_nova_conta
from app import main_page


def criar_tabelas():
    # Conectando aos bancos de dados
    conn_credenciais = sqlite3.connect('banco_sql/credenciais.db')
    conn_clientes = sqlite3.connect('banco_sql/clientes.db')
    conn_acesso = sqlite3.connect('banco_sql/acesso_cliente.db')

    # Criar tabela de credenciais
    conn_credenciais.execute('''CREATE TABLE IF NOT EXISTS credenciais (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                usuario TEXT UNIQUE,
                                senha TEXT)''')

    # Criar tabela de clientes
    conn_clientes.execute('''CREATE TABLE IF NOT EXISTS clientes (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                usuario TEXT UNIQUE,
                                nome TEXT,
                                telefone TEXT UNIQUE,
                                data_nascimento DATE,
                                rua TEXT,
                                numero TEXT,
                                bairro TEXT,
                                cidade TEXT,
                                estado TEXT,
                                pais TEXT,
                                cep TEXT)''')

    # Criar tabela de acesso cliente
    conn_acesso.execute('''CREATE TABLE IF NOT EXISTS acesso_cliente (
                                cliente_id INTEGER,
                                data_limite DATE,
                                bypass INTEGER,
                                FOREIGN KEY (cliente_id) REFERENCES clientes (id))''')

    conn_credenciais.commit()
    conn_clientes.commit()
    conn_acesso.commit()

    conn_credenciais.close()
    conn_clientes.close()
    conn_acesso.close()


def main():
    # Inicializa o controlador de cookies
    controller = CookieController()

    # Verifica se o usuário está logado
    logged_in = controller.get('logged_in')

    print(f'Main: O logged_in é: {logged_in}')

    if logged_in is True:
        st.session_state.cliente_id = controller.get('cliente_id')
        main_page(controller)
    elif logged_in is False:
        st.sidebar.title("Menu")
        opcao = st.sidebar.radio("Selecione uma opção", ["Login", "Criar Conta"])

        if opcao == "Login":
            login(controller)  # Passa o controlador de cookies para a função de login
        elif opcao == "Criar Conta":
            criar_nova_conta()


if __name__ == "__main__":
    main()
