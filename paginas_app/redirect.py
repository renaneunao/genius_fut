import streamlit as st
from streamlit_cookies_controller import CookieController, RemoveEmptyElementContainer
from dotenv import load_dotenv
import os

administrador = 3

# Carrega as variáveis de ambiente
load_dotenv()
api_key_openai = os.getenv("OPENAI_API_KEY")

dias_acesso = 3

# Configuração da página
st.set_page_config(page_title="GeniusFut", page_icon="icone_mini.png")

# Inicializa o controlador de cookies
controller = CookieController(key='cookies')
RemoveEmptyElementContainer()

cliente_id = controller.get('cliente_id')
logged_in = controller.get('logged_in')

if not cliente_id:
    st.switch_page("paginas_app/login.py")  # Redireciona para a página de login
else:
    st.switch_page("paginas_app/app.py")  # Redireciona para a página de login

