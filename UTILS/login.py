import mysql.connector
import time
from UTILS.connection import get_connection


def verificar_login(controller, usuario, senha):
    print(f'Logged_In Verificar Login: {controller.get("logged_in")}')
    print(f'Cliente Verificar Login: {controller.get("cliente_id")}')

    conn = get_connection()

    cursor = conn.cursor()
    cursor.execute('SELECT id FROM credenciais WHERE usuario = %s AND senha = %s', (usuario, senha))
    data = cursor.fetchone()
    conn.close()

    return data  # Retorna apenas o id


def login(st, controller):
    controller.set('logged_in', False)  # Remover o estado de login
    controller.set('cliente_id', False)  # Opcional: limpar o cliente_id
    print(f'Logged_In Main: {controller.get("logged_in")}')
    print(f'Cliente Main: {controller.get("cliente_id")}')

    # Verifica se o usuário está logado
    logged_in = controller.get('logged_in')
    cliente_id = controller.get('cliente_id')

    while logged_in is None:
        logged_in = controller.get('logged_in')
        # Pausa para evitar sobrecarga no processamento
        time.sleep(1)  # Aguarda 1 segundo antes de verificar novamente

    while cliente_id is None:
        cliente_id = controller.get('cliente_id')
        # Pausa para evitar sobrecarga no processamento
        time.sleep(1)  # Aguarda 1 segundo antes de verificar novamente

    st.title("Login")
    usuario = st.text_input("Usuário", key='text_input_usuario_login')
    senha = st.text_input("Senha", type='password', key='text_input_password_login')

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Entrar"):
            credenciais = verificar_login(controller, usuario, senha)
            if credenciais:
                cliente_id = credenciais[0]
                controller.set('logged_in', True)
                controller.set('cliente_id', cliente_id)
                st.success("Login bem-sucedido! Bem-vindo à tela principal.")
                st.rerun()  # Recarrega a página após o login bem-sucedido
            else:
                st.error("Usuário ou senha incorretos.")

    with col2:
        # Botão para ir à tela de criar nova conta
        if st.button("Criar nova conta"):
            st.session_state['screen'] = 'criar_conta'  # Muda a tela para criação de conta
            st.rerun()
