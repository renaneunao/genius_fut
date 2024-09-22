import streamlit as st
import sqlite3
from datetime import datetime

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

    # Criar tabela de clientes com campos detalhados de endereço
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


def criar_conta(usuario, senha, nome, telefone, data_nascimento, rua, numero, bairro, cidade, estado, pais, cep):
    conn_credenciais = sqlite3.connect('banco_sql/credenciais.db')
    conn_clientes = sqlite3.connect('banco_sql/clientes.db')

    try:
        # Verificar se o telefone já existe no banco de clientes
        cursor_clientes = conn_clientes.cursor()
        cursor_clientes.execute('SELECT * FROM clientes WHERE telefone = ?', (telefone,))
        if cursor_clientes.fetchone():
            st.error("Já existe uma conta com este número de telefone.")
            return

        # Verificar se o usuário já existe no banco de credenciais
        cursor_credenciais = conn_credenciais.cursor()
        cursor_credenciais.execute('SELECT * FROM credenciais WHERE usuario = ?', (usuario,))
        if cursor_credenciais.fetchone():
            st.error("Já existe uma conta com este nome de usuário.")
            return

        # Inserir credenciais
        conn_credenciais.execute('INSERT INTO credenciais (usuario, senha) VALUES (?, ?)', (usuario, senha))
        conn_credenciais.commit()

        # Inserir informações pessoais no banco de clientes
        conn_clientes.execute('''INSERT INTO clientes (usuario, nome, telefone, data_nascimento, rua, numero, bairro, cidade, estado, pais, cep)
                                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                              (usuario, nome, telefone, data_nascimento, rua, numero, bairro, cidade, estado, pais, cep))
        conn_clientes.commit()
        st.success("Conta criada com sucesso!")
    except sqlite3.IntegrityError as e:
        st.error(f"Erro de integridade ao criar conta: {str(e)}")
    except Exception as e:
        st.error(f"Erro inesperado: {str(e)}")  # Captura outros erros
    finally:
        conn_credenciais.close()
        conn_clientes.close()

def verificar_login(usuario, senha):
    conn = sqlite3.connect('banco_sql/credenciais.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM credenciais WHERE usuario = ? AND senha = ?', (usuario, senha))
    data = cursor.fetchone()
    conn.close()

    return data  # Retorna apenas o id


def verificar_acesso(cliente_id):
    conn = sqlite3.connect('banco_sql/acesso_cliente.db')
    cursor = conn.cursor()
    cursor.execute('SELECT data_limite, bypass FROM acesso_cliente WHERE cliente_id = ?', (cliente_id,))
    data = cursor.fetchone()
    conn.close()

    if data:
        data_limite, bypass = data
        hoje = datetime.now().date()
        if bypass or datetime.strptime(data_limite, "%Y-%m-%d").date() >= hoje:
            return True
        else:
            return False
    return False


def login(controller):
    # Verifica se o usuário está logado
    logged_in = controller.get('logged_in')
    print(f'Login: O logged_in é: {logged_in}')
    if logged_in == False:
        controller.set('logged_in', False)
    st.title("Login")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type='password')

    if st.button("Entrar"):
        print(f"Tentando login com usuário: {usuario}")  # Print para depuração
        credenciais = verificar_login(usuario, senha)
        if credenciais:
            # Verificar se o cliente_id existe na tabela clientes
            conn_clientes = sqlite3.connect('banco_sql/clientes.db')
            cursor_clientes = conn_clientes.cursor()
            cursor_clientes.execute('SELECT id FROM clientes WHERE usuario = ?', (usuario,))
            cliente = cursor_clientes.fetchone()
            conn_clientes.close()

            if cliente:
                cliente_id = cliente[0]
                if verificar_acesso(cliente_id):
                    st.write(f'Já verifiquei o acesso')
                    st.session_state.cliente_id = cliente_id  # Armazenar cliente_id na sessão
                    st.success("Login bem-sucedido! Bem-vindo à tela principal.")

                    # Armazena os cookies
                    controller.set('logged_in', True)
                    controller.set('cliente_id', cliente_id)
                    print('Settando logged_in como True')

                    st.rerun()  # Redireciona após login
                else:
                    st.error("Acesso negado. Verifique a data limite ou contate o suporte.")
            else:
                st.error("Cliente não encontrado.")
        else:
            st.error("Usuário ou senha incorretos.")

def criar_nova_conta():
    st.title("Criar Nova Conta")

    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type='password')
    confirmar_senha = st.text_input("Confirmar Senha", type='password')
    nome = st.text_input("Nome Completo")
    telefone = st.text_input("Telefone")
    data_nascimento = st.date_input("Data de Nascimento")

    # Campos de endereço detalhado
    rua = st.text_input("Rua")
    numero = st.text_input("Número")
    bairro = st.text_input("Bairro")
    cidade = st.text_input("Cidade")
    estado = st.text_input("Estado")
    pais = st.text_input("País")
    cep = st.text_input("CEP")

    if st.button("Criar Conta"):
        if senha != confirmar_senha:
            st.error("As senhas não correspondem!")
        else:
            criar_conta(usuario, senha, nome, telefone, data_nascimento, rua, numero, bairro, cidade, estado, pais, cep)


