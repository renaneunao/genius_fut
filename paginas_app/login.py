from UTILS.connection import get_connection
from UTILS.utils import verificar_cookies
import streamlit as st
from streamlit_cookies_controller import CookieController, RemoveEmptyElementContainer
import time

controller = CookieController(key='cookies')
RemoveEmptyElementContainer()

# cookies = controller.getAll()
# st.write(cookies)

def verificar_login(usuario, senha):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM credenciais WHERE usuario = %s AND senha = %s', (usuario, senha))
    data = cursor.fetchone()
    conn.close()

    return data


cliente_id, logged_in = verificar_cookies(controller)

st.title("Login")
usuario = st.text_input("Usuário", key='text_input_usuario_login')
senha = st.text_input("Senha", type='password', key='text_input_password_login')

col1, col2 = st.columns(2)
with col1:
    if st.button("Entrar"):
        credenciais = verificar_login(usuario, senha)
        if credenciais:
            cliente_id = credenciais[0]
            controller.set('logged_in', True)
            controller.set('cliente_id', cliente_id)
            with st.spinner('Inicializando...'):
                time.sleep(1)
                st.switch_page("paginas_app/app.py")  # Redireciona para a página de login
        else:
            st.error("Usuário ou senha incorretos.")

with col2:
    # Botão para ir à tela de criar nova conta
    if st.button("Criar nova conta"):
        st.switch_page("paginas_app/criar_conta.py")  # Redireciona para a página de login

