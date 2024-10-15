from streamlit_cookies_controller import CookieController
import streamlit as st
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
llm = ChatOpenAI(model_name="gpt-4o-mini", openai_api_key=api_key_openai, temperature=0)

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
    /* Aplica o tamanho da fonte a todos os <p> dentro da estrutura desejada */
    div > label > div > div > div > p {
        font-size: 12px; /* Ajusta o tamanho da fonte para 8px */
        white-space: nowrap; /* Evita quebra de palavras */
    }
    /* Ajusta a altura do sidebar dentro do bottom container usando data-testid */
    div > div > div > div > div > div > details > div {
        height: 80px;  /* Ajuste o valor conforme necessário */
        overflow: hidden;  /* Para evitar que conteúdo excedente apareça */
    }
    /* Ajusta a altura do bottom container usando data-testid */
    [data-testid="stBottomBlockContainer"] {
        height: 50px; /* Ajuste este valor conforme necessário */
        padding: 0;   /* Remove o padding se necessário */
    }
    /* Background verde para o expander do bottom */
    div > div > div > div > div > div > details > summary {
        background-color: #39FF14;  /* Fundo verde neon */
        color: black;  /* Fonte branca */
        font-weight: bold;  /* Para destacar ainda mais */
        padding: 5px;  /* Para um pouco de espaçamento interno */
        border-radius: 8px;  /* Cantos arredondados */
    }
    /* Estilo para o botão em verde neon */
    .stButton {
        padding-top: 20px;  /* Espaçamento superior de 20px */
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

    if logged_in is True:
        pass

        main_page(st, controller, administrador, llm)  # Trecho adicionado para passar pelo bug, remover depois.
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
