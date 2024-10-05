from streamlit_cookies_controller import CookieController
import streamlit as st
from datetime import datetime
import time
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

from UTILS.criar_conta import criar_nova_conta
from UTILS.login import login
from app import main_page

load_dotenv()
api_key_openai = os.getenv("OPENAI_API_KEY")

administrador = 'Renan Barbosa Silva Vianna'
dias_acesso = 3
premium = False
llm = ChatOpenAI(model_name="gpt-4o-mini", openai_api_key=api_key_openai)

st.set_page_config(page_title="GeniusFut", page_icon="icone_mini.png")

st.markdown(
    r"""
    <style>
    /* Oculta o botão Deploy */
    #root > div:nth-child(1) > div.withScreencast > div > div > header > div.st-emotion-cache-15ecox0.ezrtsby0 > div.stAppDeployButton {
        display: none; /* Oculta todo o contêiner do botão Deploy */
    }

    /* Remove margens e padding adicionais do aplicativo */
    .stApp {
        margin: 0; /* Remove margens ao redor do aplicativo */
        padding: 0; /* Remove padding ao redor do aplicativo */
    }

    /* Bloquear o redimensionamento da sidebar */
    [data-testid="stSidebar"] {
        min-width: 250px; /* Definir a largura mínima da sidebar */
        max-width: 250px; /* Definir a largura máxima da sidebar */
        width: 250px;     /* Definir uma largura fixa */
    }

    /* Ajusta a altura do bottom container usando data-testid */
    [data-testid="stBottomBlockContainer"] {
        height: 105px; /* Ajuste este valor conforme necessário */
        padding: 0;   /* Remove o padding se necessário */
    }
    """,
    unsafe_allow_html=True
)

# Inicializa o controlador de cookies
controller = CookieController()

# Variável para controlar a tela atual (login ou criar conta)
if 'screen' not in st.session_state:
    st.session_state['screen'] = 'login'  # Tela padrão é a de login


def main():
    # Verifica se o usuário está logado e o cliente_id
    while (logged_in := controller.get('logged_in')) is None:
        time.sleep(0.1)

    while (cliente_id := controller.get('cliente_id')) is None:
        time.sleep(0.1)

    # Obtem a data de vencimento do controlador de cookies
    data_vencimento = controller.get('data_limite')

    if isinstance(data_vencimento, str):
        try:
            data_vencimento = datetime.strptime(data_vencimento, '%Y-%m-%d')  # Ajuste o formato conforme necessário
        except ValueError:
            st.error("Formato de data inválido.")
            data_vencimento = None

    if logged_in is True:
        # Verifica se a data de vencimento é menor que a data atual
        if data_vencimento is not None and data_vencimento < datetime.today():
            st.error("Sua licença venceu. Por favor, adquira uma nova licença.")
            # time.sleep(3)
            # Trecho desabilitado por enquanto. Criar depois uma lógica de vendas integrada.
            # controller.set('logged_in', False)  # Redefine o estado de login
            # controller.set('cliente_id', False)
            # login(controller)

        main_page(st, controller, premium, administrador, llm)  # Trecho adicionado para passar pelo bug, remover depois.
    elif logged_in is False:
        if st.session_state['screen'] == 'login':
            login(st, controller)
        elif st.session_state['screen'] == 'criar_conta':
            criar_nova_conta(st, controller, dias_acesso)
        else:
            login(st, controller)
        

if __name__ == "__main__":
    # Verifica se o usuário está logado
    logged_in = controller.get('logged_in')
    if logged_in is None:
        if st.button('Primeiro login?'):
            if 'screen' not in st.session_state:
                st.session_state['screen'] = 'login'
            controller.set('logged_in', False)
            controller.set('cliente_id', False)
            st.rerun()
        st.image('logo_atualizada.png', use_column_width=True)
    main()
