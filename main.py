from streamlit_cookies_controller import CookieController
import streamlit as st
import requests
import pandas as pd
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import mysql.connector
from PIL import Image, ImageDraw
import base64
import pytz
import time

from streamlit_extras.colored_header import colored_header
from streamlit_extras.bottom_container import bottom
from streamlit_extras.grid import grid


administrador = 'Renan Barbosa Silva Vianna'
dias_acesso = 3
premium = False

st.set_page_config(page_title="GeniusFut", page_icon="icone_mini.png")
# Remover o botão de Deploy e ajustar o espaço em branco
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

    /* Ajuste outros elementos se necessário */
    </style>
    """,
    unsafe_allow_html=True
)

# Inicializa o controlador de cookies
controller = CookieController()

# Variável para controlar a tela atual (login ou criar conta)
if 'screen' not in st.session_state:
    st.session_state['screen'] = 'login'  # Tela padrão é a de login

def criar_tabelas():
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


def criar_nova_conta():
    print(f'Logged_In Criar Nova Conta: {controller.get('logged_in')}')
    print(f'Cliente Criar Nova Conta: {controller.get('cliente_id')}')
    st.title("Criar Nova Conta")

    # Inputs do usuário
    usuario = st.text_input("Usuário", key='text_input_criar_usuario')
    senha = st.text_input("Senha", type='password', key='text_input_criar_senha')
    confirmar_senha = st.text_input("Confirmar Senha", type='password', key='text_input_criar_confirmar_senha')
    nome = st.text_input("Nome Completo", key='text_input_criar_nome_completo')
    telefone = st.text_input("Telefone", key='text_input_criar_telefone')
    data_nascimento = st.date_input("Data de Nascimento", format="DD/MM/YYYY", key='text_input_criar_data_nascimento')
    pais = st.text_input("País", key='text_input_criar_pais')

    col1, col2 = st.columns(2)
    with col1:
        # Validação ao clicar no botão "Criar Conta"
        if st.button("Criar Conta"):
            # Verificar se todos os campos estão preenchidos
            if not usuario or not senha or not confirmar_senha or not nome or not telefone or not data_nascimento or not pais:
                st.error("Todos os campos são obrigatórios!")
                return

            # Verificar se as senhas correspondem
            if senha != confirmar_senha:
                st.error("As senhas não correspondem!")
                return

            # Se as validações passarem, criar a conta
            criar_conta(usuario, senha, nome, telefone, data_nascimento, pais)

    with col2:
        # Botão para voltar à tela de login
        if st.button("Já tem uma conta? Faça login"):
            st.session_state['screen'] = 'login'  # Muda a tela para login
            st.rerun()


def criar_conta(usuario, senha, nome, telefone, data_nascimento, pais):
    print(f'Logged_In Criar Conta: {controller.get('logged_in')}')
    print(f'Cliente Criar Conta: {controller.get('cliente_id')}')
    conn = mysql.connector.connect(
        host='geniusfut.c7k02g0my0as.us-east-2.rds.amazonaws.com',
        user='renaneunao',
        password='*Vitorya111',
        database='geniusfut_database',
        port=3306
    )

    cursor = conn.cursor()
    try:
        # Verificar se o telefone já existe no banco de clientes
        cursor.execute('SELECT * FROM clientes WHERE telefone = %s', (telefone,))
        if cursor.fetchone():
            st.error("Já existe uma conta com este número de telefone.")
            return

        # Verificar se o usuário já existe no banco de credenciais
        cursor.execute('SELECT * FROM credenciais WHERE usuario = %s', (usuario,))
        if cursor.fetchone():
            st.error("Já existe uma conta com este nome de usuário.")
            return

        # Inserir credenciais
        cursor.execute('INSERT INTO credenciais (usuario, senha) VALUES (%s, %s)', (usuario, senha))

        # Inserir informações pessoais no banco de clientes
        cursor.execute('''INSERT INTO clientes (usuario, nome, telefone, data_nascimento, pais) 
                          VALUES (%s, %s, %s, %s, %s)''',
                       (usuario, nome, telefone, data_nascimento, pais))

        # Obter o ID do cliente recém inserido
        cliente_id = cursor.lastrowid

        # Calcular a data limite para o acesso do cliente
        data_limite = datetime.today() + timedelta(days=dias_acesso)

        # Inserir registro de acesso do cliente
        cursor.execute('INSERT INTO acesso_cliente (cliente_id, data_limite, bypass) VALUES (%s, %s, %s)',
                       (cliente_id, data_limite, 0))

        conn.commit()
        st.success("Conta criada com sucesso!")

    except mysql.connector.IntegrityError as e:
        st.error(f"Erro de integridade ao criar conta: {str(e)}")
    except Exception as e:
        st.error(f"Erro inesperado: {str(e)}")
    finally:
        cursor.close()
        conn.close()


def verificar_login(usuario, senha):
    print(f'Logged_In Verificar Login: {controller.get('logged_in')}')
    print(f'Cliente Verificar Login: {controller.get('cliente_id')}')
    conn = mysql.connector.connect(
        host='geniusfut.c7k02g0my0as.us-east-2.rds.amazonaws.com',
        user='renaneunao',
        password='*Vitorya111',
        database='geniusfut_database',
        port=3306
    )

    cursor = conn.cursor()
    cursor.execute('SELECT id FROM credenciais WHERE usuario = %s AND senha = %s', (usuario, senha))
    data = cursor.fetchone()
    conn.close()

    return data  # Retorna apenas o id


def verificar_acesso(cliente_id):
    print(f'Logged_In Verificar Acesso: {controller.get('logged_in')}')
    print(f'Cliente Verificar Acesso: {controller.get('cliente_id')}')
    conn = mysql.connector.connect(
        host='geniusfut.c7k02g0my0as.us-east-2.rds.amazonaws.com',
        user='renaneunao',
        password='*Vitorya111',
        database='geniusfut_database',
        port=3306
    )
    cursor = conn.cursor()
    cursor.execute('SELECT data_limite, bypass FROM acesso_cliente WHERE cliente_id = %s', (cliente_id,))
    data = cursor.fetchone()
    conn.close()

    if data:
        data_limite, bypass = data
        hoje = datetime.now().date()

        # Verifica se data_limite é uma string antes de tentar converter
        if isinstance(data_limite, str):
            data_limite = datetime.strptime(data_limite, "%Y-%m-%d").date()  # Converte string para date

        # Agora você pode comparar diretamente
        if bypass or data_limite >= hoje:
            return True
        else:
            return False
    return False


def add_rounded_corners(image_path, radius):
    img = Image.open(image_path).convert("RGBA")

    # Criar uma máscara
    mask = Image.new("L", img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, img.size[0], img.size[1]), radius=radius, fill=255)

    # Aplicar a máscara à imagem
    rounded_img = Image.new("RGBA", img.size)
    rounded_img.paste(img, (0, 0), mask)

    return rounded_img


def login(controller):
    print(f'Logged_In Login: {controller.get("logged_in")}')
    print(f'Cliente Login: {controller.get("cliente_id")}')
    
    logged_in = controller.get('logged_in')
    
    if not logged_in:
        controller.set('logged_in', False)
        controller.set('cliente_id', False)
        
        # Aguardar até que o cliente_id seja False
        while controller.get('cliente_id') is None:
            print(f'Aguardando cliente_id ser False. Valor atual: {controller.get("cliente_id")}')
            time.sleep(1)  # Aguardar 1 segundo antes de verificar novamente
        
        print(f'cliente_id agora é {controller.get('cliente_id')}. Saindo do loop.')

    print(f'Aqui eu deveria carregar todo o conteudo da pagina login')
    time.sleep(10)

    st.title("Login")
    usuario = st.text_input("Usuário", key='text_input_usuario_login')
    senha = st.text_input("Senha", type='password', key='text_input_password_login')

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Entrar"):
            credenciais = verificar_login(usuario, senha)
            if credenciais:
                conn = mysql.connector.connect(
                    host='geniusfut.c7k02g0my0as.us-east-2.rds.amazonaws.com',
                    user='renaneunao',
                    password='*Vitorya111',
                    database='geniusfut_database',
                    port=3306
                )

                cursor_clientes = conn.cursor()
                cursor_clientes.execute('SELECT id FROM clientes WHERE usuario = %s', (usuario,))
                cliente = cursor_clientes.fetchone()

                if cliente:
                    cliente_id = cliente[0]
                    cursor_acessos = conn.cursor()
                    cursor_acessos.execute('SELECT data_limite, bypass FROM acesso_cliente WHERE cliente_id = %s',
                                           (cliente_id,))
                    acesso = cursor_acessos.fetchone()

                    conn.close()  # Fechar a conexão após obter os dados

                    if acesso:
                        data_limite, bypass = acesso
                        controller.set('data_limite',
                                       data_limite.strftime('%Y-%m-%d'))  # Converter para string no formato ISO

                        controller.set('bypass', bypass)

                        # Verificar se a data limite é menor que hoje e o bypass é zero
                        if data_limite < datetime.now().date() and bypass == 0:
                            st.error("Acesso negado. É necessário comprar uma licença.")
                        else:
                            if verificar_acesso(cliente_id):
                                st.success("Login bem-sucedido! Bem-vindo à tela principal.")

                                # Armazena os cookies
                                controller.set('logged_in', True)
                                controller.set('cliente_id', cliente_id)
                                main()
                                st.rerun()
                            else:
                                st.error("Acesso negado. Verifique a data limite ou contate o suporte.")
                    else:
                        st.error("Nenhum acesso encontrado para este cliente.")
                else:
                    st.error("Cliente não encontrado.")
            else:
                st.error("Usuário ou senha incorretos.")

    with col2:
        # Botão para ir à tela de criar nova conta
        if st.button("Criar nova conta"):
            st.session_state['screen'] = 'criar_conta'  # Muda a tela para criação de conta
            st.rerun()

def main_page(controller):
    print(f'Logged_In Main Page: {controller.get('logged_in')}')
    print(f'Cliente Main Page: {controller.get('cliente_id')}')
    selected_country = None
    selected_league = None
    fixture_id = None
    home_team_name = None
    away_team_name = None
    predictions = None
    home_team_logo_url = None
    away_team_logo_url = None
    selected_game_info = None

    # Exibir a imagem na sidebar
    st.sidebar.image('logo_atualizada.png', use_column_width=True)

    def get_base64_image(image_path):
        with open(image_path, "rb") as img_file:
            encoded_string = base64.b64encode(img_file.read()).decode()
        return encoded_string

    # Converte a imagem em base64
    icon_base64 = get_base64_image("icone_mini.png")

    # Usa HTML embutido no Markdown para mostrar o título e o ícone juntos
    st.markdown(
        f"""
        <h1 style="display: flex; align-items: center;">
            GeniusFut
            <img src="data:image/png;base64,{icon_base64}" style="height: 60px; margin-left: 10px;">
        </h1>
        """,
        unsafe_allow_html=True
    )

    controller.set('logged_in', True, 'ck_logged_in')
    cliente_id = controller.get('cliente_id')
    if cliente_id is not None:
        conn = mysql.connector.connect(
            host='geniusfut.c7k02g0my0as.us-east-2.rds.amazonaws.com',
            user='renaneunao',
            password='*Vitorya111',
            database='geniusfut_database',
            port=3306
        )

        cursor = conn.cursor()

        # Usar %s como placeholder no MySQL
        cursor.execute("SELECT nome FROM clientes WHERE id = %s", (cliente_id,))
        cliente = cursor.fetchone()

        if cliente:  # Verifica se o cliente não é None
            nome_cliente = cliente[0]
            colored_header(
                label=f"Bem-vindo, {nome_cliente}!",
                description="Aqui o GREEN é certo!",
                color_name="green-70",
            )
        else:
            nome_cliente = ''
            st.write("Cliente não encontrado.")
            st.sidebar.image('logo_atualizada.png', use_column_width=True)
            login(controller)
            st.rerun()

        conn.close()

        # Carregar a chave da API do OpenAI do arquivo .env
        load_dotenv()
        api_key_openai = os.getenv("OPENAI_API_KEY")
        api_key_rapidapi = os.getenv("X-RAPIDAPI-KEY")

        @st.cache_data
        def fetch_timezones():
            url = "https://api-football-v1.p.rapidapi.com/v3/timezone"
            headers = {
                'x-rapidapi-key': api_key_rapidapi,
                'x-rapidapi-host': "api-football-v1.p.rapidapi.com"
            }
            response = requests.get(url, headers=headers)
            timezones_data = response.json()
            return timezones_data.get('response', [])

        # Função para obter dados de países
        @st.cache_data
        def fetch_countries():
            url = "https://api-football-v1.p.rapidapi.com/v3/countries"
            headers = {
                'x-rapidapi-key': api_key_rapidapi,
                'x-rapidapi-host': "api-football-v1.p.rapidapi.com"
            }
            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                countries_data = response.json()
                return countries_data.get('response', [])
            except requests.RequestException as e:
                st.error(f"Erro ao buscar países: {e}")
                return []

        # Função para obter ligas para um país específico
        @st.cache_data
        def fetch_leagues(country_name):
            url = "https://api-football-v1.p.rapidapi.com/v3/leagues"
            headers = {
                'x-rapidapi-key': api_key_rapidapi,
                'x-rapidapi-host': "api-football-v1.p.rapidapi.com"
            }
            params = {"country": country_name}
            response = requests.get(url, headers=headers, params=params)
            leagues_data = response.json()
            # print("Leagues Data:", leagues_data)  # Debug
            return leagues_data.get('response', [])

        def fetch_fixtures(date, league_id, timezone):
            url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
            headers = {
                'x-rapidapi-key': api_key_rapidapi,
                'x-rapidapi-host': "api-football-v1.p.rapidapi.com"
            }
            params = {
                "date": date,
                "league": league_id,
                "season": season,
                "timezone": timezone  # Utiliza o timezone selecionado
            }
            response = requests.get(url, headers=headers, params=params)
            fixtures_data = response.json()
            return fixtures_data.get('response', [])

        # Função para obter estatísticas do time
        @st.cache_data
        def fetch_team_stats(season, team_id):
            url = "https://api-football-v1.p.rapidapi.com/v3/standings"
            headers = {
                'x-rapidapi-key': api_key_rapidapi,
                'x-rapidapi-host': "api-football-v1.p.rapidapi.com"
            }
            params = {"season": season, "team": team_id}
            response = requests.get(url, headers=headers, params=params)
            standings_data = response.json()

            if standings_data.get('response'):
                team_stats = standings_data['response'][0]['league']['standings'][0][0]
                return team_stats
            else:
                return None

        def stats_to_dataframe(team_stats, team_name):
            if team_stats:
                data = {
                    "Tipo": ["Casa", "Fora", "Total"],
                    "Jogos": [
                        team_stats.get('home', {}).get('played', 0),
                        team_stats.get('away', {}).get('played', 0),
                        team_stats.get('all', {}).get('played', 0)
                    ],
                    "Vitórias": [
                        team_stats.get('home', {}).get('win', 0),
                        team_stats.get('away', {}).get('win', 0),
                        team_stats.get('all', {}).get('win', 0)
                    ],
                    "Gols Marcados": [
                        team_stats.get('home', {}).get('goals', {}).get('for', 0),
                        team_stats.get('away', {}).get('goals', {}).get('for', 0),
                        team_stats.get('all', {}).get('goals', {}).get('for', 0)
                    ],
                    "Gols Sofridos": [
                        team_stats.get('home', {}).get('goals', {}).get('against', 0),
                        team_stats.get('away', {}).get('goals', {}).get('against', 0),
                        team_stats.get('all', {}).get('goals', {}).get('against', 0)
                    ]
                }

                df = pd.DataFrame(data)

                # Calcular as médias
                df["Média de Gols Marcados"] = df["Gols Marcados"] / df["Jogos"].replace(0, pd.NA)
                df["Média de Gols Sofridos"] = df["Gols Sofridos"] / df["Jogos"].replace(0, pd.NA)

                # Centralizar os dados no DataFrame usando st.table
                st.subheader(f"Estatísticas de {team_name}")
                st.table(df.style.set_properties(**{'text-align': 'center'}))

                return df
            else:
                st.write(f"Estatísticas para {team_name} não disponíveis.")

        # Sidebar para timezone
        timezones = fetch_timezones()

        # Timezone padrão
        default_timezone = "America/Sao_Paulo"
        selected_timezone = default_timezone
        timezone = pytz.timezone(selected_timezone)

        # Selecionar a data do jogo
        today = datetime.now(timezone).date()
        date = st.sidebar.date_input(
            "Selecione a data do jogo desejado:",
            today,
            min_value=today,  # opcional: define a data mínima como hoje
            format="DD/MM/YYYY"
        )

        # Simulação de uma data de vencimento
        data_vencimento = controller.get('data_limite')

        try:
            data_vencimento = datetime.strptime(data_vencimento, '%Y-%m-%d')
            st.sidebar.markdown(
                f"<span style='font-size: 12px;'>📅 Vencimento: {data_vencimento.strftime('%d/%m/%Y')}</span>",
                unsafe_allow_html=True)
        except ValueError:
            st.sidebar.markdown("<span style='font-size: 12px;'>📅 Data de Vencimento: Não disponível.</span>",
                                unsafe_allow_html=True)

        # # Selecionar a data do jogo
        # date = st.sidebar.date_input("Selecione a data do jogo desejado:", pd.to_datetime('today').tz_localize(br_tz),
        #                              format="DD/MM/YYYY")

        # Extraindo o ano da data escolhida para a temporada
        season = pd.to_datetime(date).year

        # Função para obter predições
        def get_prediction(fixture_id):
            url = f"https://api-football-v1.p.rapidapi.com/v3/predictions?fixture={fixture_id}"
            headers = {
                'x-rapidapi-key': api_key_rapidapi,
                'x-rapidapi-host': "api-football-v1.p.rapidapi.com"
            }
            response = requests.get(url, headers=headers)
            predictions_data = response.json()

            if 'response' in predictions_data and predictions_data['response']:
                prediction = predictions_data['response'][0]  # Assuming only one prediction per fixture

                # Extracting information safely
                home_team = prediction.get('teams', {}).get('home', {})
                away_team = prediction.get('teams', {}).get('away', {})

                # Corrigindo a extração dos IDs das equipes
                team_id_home = home_team.get('id')  # Obter o ID do time da casa
                team_id_away = away_team.get('id')  # Obter o ID do time visitante

                if home_team is None or away_team is None:
                    return 'N/A', 'N/A', 'No data available', 'No advice available', 'No data available', 'No data available', 'No advice available'

                home_team_last_5_games = home_team.get('league', {}).get('form', [])
                away_team_last_5_games = away_team.get('league', {}).get('form', [])

                home_team_last_5_games = home_team_last_5_games[-5:] if home_team_last_5_games else "No data available"
                away_team_last_5_games = away_team_last_5_games[-5:] if away_team_last_5_games else "No data available"

                home_team_logo_url = home_team.get('logo', 'N/A')
                away_team_logo_url = away_team.get('logo', 'N/A')
                home_team_name = home_team.get('name', 'N/A')
                away_team_name = away_team.get('name', 'N/A')

                # Mapping results to colored dots
                color_map = {'W': '🟢', 'L': '🔴', 'D': '⚪'}

                home_team_last_5_games = ''.join(color_map.get(result, result) for result in home_team_last_5_games)
                away_team_last_5_games = ''.join(color_map.get(result, result) for result in away_team_last_5_games)

                # Obter previsões
                predictions = prediction.get('predictions', 'No advice available')

                # Returning DataFrame and prediction text
                return (home_team_logo_url,
                        away_team_logo_url,
                        home_team_name,
                        away_team_name,
                        home_team_last_5_games,
                        away_team_last_5_games,
                        predictions,
                        team_id_home,
                        team_id_away)
            else:
                # Return default values if no data is available
                return 'N/A', 'N/A', 'No data available', 'No advice available', 'No data available', 'No data available', 'No advice available', None, None

        @st.cache_data  # Cache para armazenar a lista de casas de apostas
        def get_bookmakers(fixture_id):
            querystring = {"fixture": fixture_id}
            response = requests.get(url, headers=headers, params=querystring)

            if response.status_code == 200:
                odds_data = response.json()
                return [bookmaker["name"] for bookmaker in odds_data["response"][0]["bookmakers"]]
            else:
                st.error("Erro ao buscar odds. Verifique o ID do fixture.")
                return []

        @st.cache_data  # Cache para armazenar odds
        def fetch_odds(fixture_id):
            response = requests.get(url, headers=headers, params={"fixture": fixture_id})

            if response.status_code == 200:
                return response.json()
            else:
                st.error("Erro ao buscar odds. Verifique o ID do fixture.")
                return None

        # Sidebar para configurações
        with st.sidebar.expander("Configurações Gerais"):
            st.title("Configurações Gerais")
            # Lista de idiomas
            languages = ['Inglês', 'Espanhol', 'Chinês', 'Hindi', 'Árabe', 'Português', 'Bengali', 'Russo', 'Japonês',
                         'Lahnda',
                         'Alemão', 'Francês', 'Coreano', 'Italiano', 'Turco', 'Vietnamita', 'Polonês', 'Ucraniano',
                         'Holandês', 'Grego']

            # Obter o idioma selecionado do cookie ou usar o primeiro idioma da lista como padrão
            selected_language_cookie = controller.get('language')
            if selected_language_cookie in languages:
                selected_language = selected_language_cookie
            else:
                selected_language = languages[5]  # Defina um valor padrão, por exemplo, o primeiro idioma da lista

            # Seleção do idioma na sidebar
            selected_language = st.selectbox("Selecione o idioma:", languages, index=languages.index(selected_language))
            controller.set('language', selected_language)

            # Campo de entrada para nome do usuário
            user_name_cookie = controller.get('user_name')

            # Usar nome_cliente como padrão se o cookie estiver vazio
            if not user_name_cookie:
                name_value = nome_cliente
            else:
                name_value = user_name_cookie

            user_name = st.text_input("Digite seu nome:", value=name_value)

            # Atualiza o cookie com o valor do nome do usuário
            controller.set('user_name', user_name)

            bet_temperature_value = controller.get('bet_temperature')

            if bet_temperature_value is not None:
                bet_temperature = float(bet_temperature_value)
            else:
                # Handle the None case (e.g., set a default value or raise an error)
                bet_temperature = 0.5  # or any other default value you want

            # Configura o slider
            bet_temperature = st.slider(
                "Defina a temperatura da aposta (0 a 1):",
                min_value=0.0,
                max_value=1.0,
                value=bet_temperature,
                step=0.1,
                help="Quanto maior a temperatura, mais arriscada a bet."
            )

            # Adiciona HTML e CSS para os emojis
            st.markdown("""
                <style>
                .slider-container {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    position: relative;
                    margin-top: -20px;
                }
                .slider-container div {
                    font-size: 15px;
                }
                .slider-container .min-emoji {
                    margin-right: 10px;
                }
                .slider-container .max-emoji {
                    margin-left: 10px;
                }
                </style>
                <div class="slider-container">
                    <div class="min-emoji">❄️</div>
                    <div class="max-emoji">🔥</div>
                </div>
                """, unsafe_allow_html=True)
            controller.set('bet_temperature', bet_temperature)

            ######################## CONFIGURAÇÃO PARA ADICIONAR ODD

            # Configurar a chave da API e a URL
            url = "https://api-football-v1.p.rapidapi.com/v3/odds"
            headers = {
                "x-rapidapi-key": "2197625affmsh6db1f3afb876a8ep153650jsn3f9195067c24",
                "x-rapidapi-host": "api-football-v1.p.rapidapi.com"
            }

            # Listas de grupos de bets categorizados
            bets_gols = [
                "Anytime Goal Scorer", "Both Teams Score", "Both Teams Score - First Half",
                "Both Teams To Score - Second Half", "Both Teams to Score in Both Halves",
                "Goals Over/Under", "Goals Over/Under - Second Half",
                "Goals Over/Under First Half", "Exact Goals Number", "Exact Goals Number - First Half",
                "Total Goals By Ranges (1st Half)", "To Score In 1st Half", "To Score in Both Halves",
                "Team To Score First", "Home Team Score a Goal", "Away Team Score a Goal",
                "Home Team Score a Goal (1st Half)", "Away Team Score a Goal (1st Half)",
                "Home Team Score a Goal (2nd Half)", "Away Team Score a Goal (2nd Half)",
                "Home team will score in both halves", "Away team will score in both halves"
            ]

            bets_escanteios = [
                "Away Corners Over/Under", "Corners 1x2", "Corners 1x2 (1st Half)", "Corners 1x2 (2nd Half)",
                "Corners Asian Handicap", "Corners Asian Handicap (1st Half)", "Corners Asian Handicap (2nd Half)",
                "Corners Over Under", "First Corner", "Home Total Corners (1st Half)", "Home Total Corners (2nd Half)",
                "Away Total Corners (1st Half)", "Away Total Corners (2nd Half)", "Total Corners (1st Half)",
                "Total Corners (2nd Half)", "Total Corners (3 way)", "Total Corners (3 way) (1st Half)",
                "Total Corners (3 way) (2nd Half)"
            ]

            bets_cartoes = [
                "Away Team Total Cards", "Home Team Total Cards", "Cards Asian Handicap", "Cards European Handicap",
                "Cards Over/Under", "Red Cards Over/Under", "Yellow Cards 1x2", "Yellow Cards 1x2 (1st Half)",
                "Yellow Cards 1x2 (2nd Half)", "Yellow Asian Handicap", "Yellow Asian Handicap (1st Half)",
                "Yellow Asian Handicap (2nd Half)", "Yellow Odd/Even", "Yellow Over/Under",
                "Yellow Over/Under (1st Half)",
                "RCARD"
            ]

            # Mapeamento de grupos de bets
            bet_groups = {
                "Bets de Gols": bets_gols,
                "Bets de Escanteios": bets_escanteios,
                "Bets de Cartões": bets_cartoes
            }

            # Obtém o valor da odd mínima configurada
            min_odd_value = controller.get('min_odd_value')

            if min_odd_value is not None:
                min_odd = float(min_odd_value)
            else:
                # Tratar o caso de None (ex: definir um valor padrão ou levantar um erro)
                min_odd = 1.1  # ou qualquer outro valor padrão que você desejar

            # Configura o slider para odd mínima
            min_odd = st.slider(
                "Defina a odd mínima (1.1 a 20):",
                min_value=1.1,
                max_value=20.0,
                value=min_odd,
                step=0.1,
                help="Defina a odd mínima para suas apostas."
            )

            # Adiciona HTML e CSS para os emojis
            st.markdown("""
                <style>
                .slider-container {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    position: relative;
                    margin-top: -20px;
                }
                .slider-container div {
                    font-size: 15px;
                }
                .slider-container .min-emoji {
                    margin-right: 10px;
                }
                .slider-container .max-emoji {
                    margin-left: 10px;
                }
                </style>
                <div class="slider-container">
                    <div class="min-emoji">🔻</div>
                    <div class="max-emoji">🔺</div>
                </div>
                """, unsafe_allow_html=True)

            # Armazena o valor da odd mínima no controller
            controller.set('min_odd_value', min_odd)

            if premium:
                default_bookmakers = ["Betfair", "Bet365", "Betano"]
                help = 'Selecione até 3 casas de apostas'
                max_selections = 3
                default_group_bets = ['Bets de Gols', 'Bets de Escanteios', 'Bets de Cartões']
            else:
                default_bookmakers = ["Bet365"]
                help = 'Selecione 1 casa de apostas'
                max_selections = 1
                default_group_bets = ['Bets de Gols']

            bookmakers_list = get_bookmakers('1180631')
            selected_bookmakers = st.multiselect(
                "Escolha até 3 casas de apostas:",
                options=bookmakers_list,
                default=[bm for bm in default_bookmakers if bm in bookmakers_list],  # Seleciona as casas padrão
                max_selections=max_selections,
                help=help
            )

            # Permitir ao usuário selecionar múltiplos grupos de bets
            selected_groups = st.multiselect(
                "Selecione um ou mais grupos de bets:",
                options=list(bet_groups.keys()),
                max_selections=1,
                default=[bet for bet in default_group_bets if bet in list(bet_groups.keys())],
                # Seleciona as casas padrão
            )

            # Expandir os grupos selecionados para incluir todas as bets
            selected_bets = []
            for group in selected_groups:
                selected_bets.extend(bet_groups[group])

            ######################### CONFIGURAÇÃO PARA ADICIONAR ODD

            # Cria um expander para o timezone
            with st.sidebar.expander(f"Horários de {default_timezone}", expanded=False):
                # Dropdown para selecionar o timezone
                selected_timezone = st.selectbox("Selecione o timezone:", timezones,
                                                 index=timezones.index(default_timezone))

                # Botão para mudar o timezone
                if st.button("🔄", key="timezone_btn"):
                    # A lógica para mudar o timezone pode ser adicionada aqui
                    st.success(f"Timezone alterado para: {selected_timezone}")

        # Alinha o botão com o texto
        if st.sidebar.button("Sair da Conta", key="logout_btn"):
            # Remover ou setar como falso o cookie de logged_in
            controller.set('logged_in', False)  # Remover o estado de login
            controller.set('cliente_id', None)  # Opcional: limpar o cliente_id
            # Redirecionar para a página de login
            st.success("Você saiu da conta.")
            login(controller)
            st.rerun()

        if nome_cliente == administrador:
            with st.sidebar.expander("Painel Administrador", expanded=True):
                admin_page()

        # Define o CSS para ajustar o layout do container específico do bottom
        st.markdown(
            """
            <style>
            /* Seleciona o elemento específico do bottom */
            #root > div:nth-child(1) > div.withScreencast > div > div > div > section.stAppViewMain.main.st-emotion-cache-bm2z3a.ea3mdgi8 > div.st-emotion-cache-1p2n2i4.ea3mdgi7 > div > div > div {
                max-width: 14000px;  /* Define a largura máxima */
                max-height: 50px;  /* Define a altura máxima */
                margin: auto;  /* Centraliza o container */
                padding: 10px;  /* Ajusta o espaçamento interno */
                background-color: #33CC00;  /* Adiciona uma cor de fundo */
                border-radius: 10px;  /* Bordas arredondadas */
            }
            </style>
            """, unsafe_allow_html=True
        )
        with bottom():
            my_grid = grid([2, 2, 2, 1], vertical_align="bottom")

            with st.spinner("Carregando países..."):
                countries = fetch_countries()

            # Buscar países
            if countries:
                country_names = [country['name'] for country in countries]

                # Selecionar o país armazenado, se disponível
                selected_country = my_grid.selectbox("Selecione o país:", country_names, index=country_names.index(
                    controller.get('selected_country')) if controller.get('selected_country') in country_names else 23)
                controller.set('selected_country', selected_country)
            else:
                st.write("Nenhum país encontrado.")

            # Buscar ligas para o país selecionado
            if selected_country:
                with st.spinner("Carregando ligas..."):
                    leagues = fetch_leagues(selected_country)
                if leagues:
                    league_names = [league['league']['name'] for league in leagues]

                    # Selecionar a liga armazenada, se disponível
                    selected_league = my_grid.selectbox("Selecione a liga:", league_names,
                                                        index=league_names.index(
                                                            controller.get('selected_league')) if controller.get(
                                                            'selected_league') in league_names else 0)
                    controller.set('selected_league', selected_league)
            else:
                st.write("Nenhuma liga encontrada para o país selecionado.")

            if selected_league:
                league_id = next(
                    (league['league']['id'] for league in leagues if
                     league['league']['name'] == selected_league), None)
                if league_id:
                    with st.spinner("Carregando jogos..."):
                        fixtures = fetch_fixtures(date, league_id, selected_timezone)
                    if fixtures:
                        games = [
                            {
                                'game_info': f"{fixture['teams']['home']['name']} vs {fixture['teams']['away']['name']} - {datetime.strptime(fixture['fixture']['date'], '%Y-%m-%dT%H:%M:%S%z').strftime('%H:%M')}",
                                'fixture_id': fixture['fixture']['id']
                            }
                            for fixture in fixtures
                        ]
                        game_options = [game['game_info'] for game in games]
                        selected_game_info = my_grid.selectbox("Escolha um jogo:", game_options)

                        if selected_game_info:
                            fixture_id = next(
                                game['fixture_id'] for game in games if
                                game['game_info'] == selected_game_info
                            )
                            # Imprimir o fixture_id selecionado
                            print(f"Fixture ID selecionado: {fixture_id}")

                            odds_data = fetch_odds(fixture_id)

                            if odds_data:
                                data = []

                                for bookmaker in odds_data["response"][0]["bookmakers"]:
                                    if bookmaker["name"] in selected_bookmakers:  # Filtrar pelas casas selecionadas
                                        for bet in bookmaker["bets"]:
                                            bet_name = bet["name"]  # Nome da bet
                                            if bet_name in selected_bets:  # Verificar se a bet está no grupo selecionado
                                                for value in bet["values"]:
                                                    odd_value = float(value["odd"])
                                                    if odd_value >= min_odd:  # Aplicar o filtro da odd mínima
                                                        data.append({
                                                            "Casa": bookmaker["name"],
                                                            "Bet": bet_name,  # Adicionar o nome da bet
                                                            "Valor": value["value"],
                                                            "Odd": value["odd"]
                                                        })

                                # Criar DataFrame
                                df_bets = pd.DataFrame(data)

                                # Mostrar DataFrame no Streamlit
                                if not df_bets.empty:
                                    pass
                                    # st.write(df_bets)
                                else:
                                    df_bets = 'Nenhuma bet. Desconsiderar.'
                                    st.warning("Nenhuma odd encontrada para as casas e bets selecionadas.")

                    else:
                        st.write("Nenhum jogo encontrado para a data e liga selecionadas.")
                        # pass
                else:
                    # pass
                    st.write("ID da liga não encontrado.")
            else:
                # pass
                st.write("Nenhuma liga encontrada para o país selecionado.")

            st.markdown(
                """
                <style>
                /* Seletor CSS do botão fornecido */
                #root > div:nth-child(1) > div.withScreencast > div > div > div > section.stAppViewMain.main.st-emotion-cache-bm2z3a.ea3mdgi8 > div.st-emotion-cache-1p2n2i4.ea3mdgi7 > div > div > div > div > div > div.st-emotion-cache-0.e1f1d6gn0 > div > div > div.st-emotion-cache-ocqkz7.e1f1d6gn5 > div.st-emotion-cache-1b2d4l5.e1f1d6gn3 > div > div > div > div > div > button {
                    background-color: black;  /* Fundo preto */
                    border: 2px solid #33CC00;  /* Define a borda verde neon */
                    border-radius: 5px;  /* Arredonda as bordas, se desejado */
                    cursor: pointer;  /* Define o cursor para pointer */
                    padding: 10px;  /* Ajusta o padding para dar um espaço */
                    color: #33CC00;  /* Define a cor do texto como verde neon */
                    transition: border-color 0.3s; /* Transição suave para a borda */
                }

                /* Efeito ao passar o mouse */
                #root > div:nth-child(1) > div.withScreencast > div > div > div > section.stAppViewMain.main.st-emotion-cache-bm2z3a.ea3mdgi8 > div.st-emotion-cache-1p2n2i4.ea3mdgi7 > div > div > div > div > div > div.st-emotion-cache-0.e1f1d6gn0 > div > div > div.st-emotion-cache-ocqkz7.e1f1d6gn5 > div.st-emotion-cache-1b2d4l5.e1f1d6gn3 > div > div > div > div > div > button:hover {
                    border-color: #00FF00;  /* Muda a cor da borda ao passar o mouse */
                }
                </style>
                """,
                unsafe_allow_html=True
            )

            # Adiciona um botão para calcular as previsões
            if selected_game_info is not None:
                if my_grid.button("►"):
                    (home_team_logo_url,
                     away_team_logo_url,
                     home_team_name,
                     away_team_name,
                     home_team_last_5_games,
                     away_team_last_5_games,
                     predictions,
                     team_id_home,
                     team_id_away) = get_prediction(fixture_id)

        if predictions is not None:
            # Display the logos and other details side by side
            col1, col2 = st.columns(2)

            with col1:
                if home_team_logo_url != 'N/A':
                    st.image(home_team_logo_url)
                    st.write(f"**{home_team_name}**")
                    st.write(home_team_last_5_games)

            with col2:
                if away_team_logo_url != 'N/A':
                    st.image(away_team_logo_url)
                    st.write(f"**{away_team_name}**")
                    st.write(away_team_last_5_games)

            # Mapping results to colored dots
            result_map = {'🟢': 'W', '🔴': 'L', '⚪': 'D'}
            home_team_last_5_results = ''.join(
                result_map.get(result, result) for result in home_team_last_5_games)
            away_team_last_5_results = ''.join(
                result_map.get(result, result) for result in away_team_last_5_games)

            # Obter estatísticas para os dois times
            home_team_stats = fetch_team_stats(season, team_id_home)
            away_team_stats = fetch_team_stats(season, team_id_away)

            # Converter estatísticas em DataFrame e exibir
            stats_casa = stats_to_dataframe(home_team_stats, "Time da Casa")
            stats_fora = stats_to_dataframe(away_team_stats, "Time Visitante")

            st.write("**Inteligência Artificial Calculando:**")

            prompt = (
                f"""
                ### 1. Orientações para Resposta:

                - **Linguagem**: Responda sempre no idioma selecionado: `{selected_language}`.
                - **Personalização**: Dirija-se a mim pelo meu nome: `{user_name}` 
                (se o nome não estiver disponível, ignore).
                - **Especialização**: Você é um especialista em apostas online, focado em fornecer 
                dicas valiosas com base nas informações disponíveis.
                - **Confiança**: Responda com a confiança de um profissional experiente em apostas, 
                alinhando sua resposta ao conteúdo fornecido.
                - **Ambiente**: Mantenha um tom descontraído e destaque a aposta principal.
                - **Cálculo de Aposta**: Apresente a aposta como resultado de uma análise cuidadosa, 
                incluindo estatísticas relevantes na tabela. Mostre apenas as equipes mencionadas na 
                aposta principal.

                ## 2. Dicas de Apostas:
                !! Nunca ofereça odd 1, principalmente na bet principal!!
                Definição de combos de apostas:
                (uma ou mais apostas que, ao serem combinadas, formam uma dupla ou uma múltipla, onde as odds 
                são multiplicadas, formando uma odd resultante. Exemplo:
                Vencedor Visitante odd 1.2 + Mais de dois gols no jogo odd 1.5. Odd resultante = [1.2 * 1.5 = 1.8].
                portanto, odd final = 1.8)
                - Abaixo, apresente uma tabela com as equipes e, ao lado, as respectivas apostas.
                - Procure na tabela de odds que será enviada o valor das odds das apostas principais, 
                e adicione à tabela se existirem. 
                Considere que o time da casa é: {home_team_name}
                Considere que o time visitante é: {away_team_name}.

                  | Time             | Aposta                  | ODD      | Casa de Apostas
                  |------------------|------------------------|--------|----------|
                  | Time Envolvido: ``  | `sua_dica_para_a_aposta` | `odd final` | `Casa de Apostas`
                  
                Caso a aposta principal seja uma dupla ou múltipla, mostre uma tabela com as odds individuais e resultante do combo.


                - Com base no seguinte JSON, alimente seu conhecimento (não mencione o JSON):
                  `{str(predictions)}`
                ## 3. Estatísticas Adicionais:
                - Utilize as estatísticas adicionais para enriquecer sua resposta                                      
                  Considere as seguintes informações:
                  - Resultados dos últimos 5 jogos do time da casa: `{home_team_last_5_results}`.
                  - Resultados dos últimos 5 jogos do time visitante: `{away_team_last_5_results}`.
                  - Estatísticas do time da casa: `{stats_casa}` (dataframe).
                  - Estatísticas do time visitante: `{stats_fora}` (dataframe).
                ## 4. Temperatura da Aposta:
                - Utilize uma escala de 0 a 1, onde 0 representa segurança extrema e 1 representa 
                risco extremo. A temperatura escolhida é `{bet_temperature}`. Não mencione a temperatura 
                diretamente; apenas a aplique em suas sugestões.

                ## 5. Sugestões de Apostas Adicionais:
                - Agora é a parte mais importante. Vou te passar uma tabela com os dados das apostas.
                Nessa tabela temos as casas de apostas, os nomes das bets, o valor específico da bet, 
                e a odd da bet.
                - Com base na temperatura, você fornecerá bets adicionais. 
                - Forneça pelo menos uma sugestão adicional de aposta. Se a temperatura for acima 
                da média, ofereça opções mais arriscadas com base nas estatísticas. Apresente essas 
                apostas em uma tabela separada, numerada. 
                - Para sugestões de under/over gols, mencione o jogo se for geral e o time 
                específico se for uma aposta focada.

                  Exemplos de sugestões com base na temperatura:
                  - Temperatura 0: uma sugestão bastante segura (talvez uma dupla desde que seja segura).
                  - Temperatura 0.5: uma ou duas sugestões (sendo uma dupla e uma simples, ou até uma multipla, sempre mantendo a segurança).
                  - Temperatura 1: três ou mais sugestões (Seja ousado. Monte simples, duplas e uma multipla, sempre mantendo a segurança).
                    
                Se as apostas incluírem duplas ou multiplas, dê a odd final sendo a multiplicação delas. 

                ## 6. Tendências de Gols:
                - Se os dados do JSON e das tabelas indicarem uma tendência de under gols, não 
                sugira apostas de over. 
                - Se indicarem uma tendência de over gols, evite sugerir under.

                ## 7. Ousadia nas Sugestões:
                - Se a temperatura estiver alta, seja ousado nas sugestões. Se a tendência for over, 
                considere incrementar a linha de gols. 
                  - Exemplos:
                    - Para uma tendência under de -3.5 gols, a sugestão pode ser -2.5 gols.
                    - Para uma tendência over de +2.5 gols, a sugestão pode ser +3.5 gols.
                    
                ## 8. Resultados:
                - Como resultado final das apostas adicionais, espero uma tabela informando a bet,
                a casa de aposta, os envolvidos, e a odd (individual de cada bet e o resultado da multiplicação)
                
                Segue agora tabela com as ODDS:
                {df_bets}
                    
                """
            )

            llm = ChatOpenAI(model_name="gpt-4o-mini", openai_api_key=api_key_openai)

            # Adiciona o spinner enquanto aguarda a resposta da LLM
            with st.spinner("Calculando previsão..."):
                # Cria a chain para lidar com o LLM
                chain = llm.invoke(prompt)

                response = chain.content
                # st.write(predictions)
                st.write(response)
        else:
            st.write("Escolha um jogo e deixe a IA calcular a previsão.")
            st.sidebar.image('logo_atualizada.png', use_column_width=True)

    else:
        print(f'Else do cliente_id: {controller.get('logged_in')}')
        print(f'Else do cliente_id: {controller.get('cliente_id')}')
        controller.set('logged_in', False)
        controller.set('cliente_id', False)
        st.image('logo_atualizada.png', use_column_width=True)
        st.write("Você não está logado. Refaça o login")
        login(controller)
        st.rerun()


def admin_page():
    print(f'Logged_In admin_page: {controller.get('logged_in')}')
    print(f'Cliente admin_page: {controller.get('cliente_id')}')
    conn = mysql.connector.connect(
        host='geniusfut.c7k02g0my0as.us-east-2.rds.amazonaws.com',
        user='renaneunao',
        password='*Vitorya111',
        database='geniusfut_database',
        port=3306
    )

    cursor = conn.cursor()

    # Título da página
    st.title("Painel do Administrador")

    # Opções de menu
    menu = st.sidebar.selectbox("Escolha uma opção:", ["Listar Clientes", "Listar Credenciais", "Listar Acessos"])

    if menu == "Listar Clientes":
        st.subheader("Clientes")

        # Listar clientes
        cursor.execute(
            "SELECT id, usuario, nome, telefone, data_nascimento, pais FROM clientes")
        clientes = cursor.fetchall()
        df_clientes = pd.DataFrame(clientes,
                                   columns=["ID", "Usuário", "Nome", "Telefone", "Data de Nascimento", "País"])

        # Exibir a lista de clientes
        st.dataframe(df_clientes)

        # Selecionar cliente para edição
        cliente_edit = st.selectbox("Selecione o ID do cliente para editar:", df_clientes["ID"])

        if cliente_edit:
            # Consultar informações do cliente selecionado
            cursor.execute("SELECT * FROM clientes WHERE id = %s", (cliente_edit,))
            cliente = cursor.fetchone()

            # Formulário para editar informações do cliente
            nome = st.text_input("Nome", value=cliente[2])
            telefone = st.text_input("Telefone", value=cliente[3])
            data_nascimento = st.date_input("Data de Nascimento", value=cliente[4], format="DD/MM/YYYY")
            pais = st.text_input("País", value=cliente[5])  # Corrigido índice para 'pais'

            if st.button("Salvar"):
                cursor.execute("""
                    UPDATE clientes 
                    SET nome = %s, telefone = %s, data_nascimento = %s, pais = %s,  
                    WHERE id = %s
                """, (nome, telefone, data_nascimento, pais, cliente_edit))
                conn.commit()
                st.success("Cliente atualizado com sucesso!")

    elif menu == "Listar Credenciais":
        st.subheader("Credenciais")

        # Listar credenciais
        cursor.execute("SELECT id, usuario FROM credenciais")
        credenciais = cursor.fetchall()
        df_credenciais = pd.DataFrame(credenciais, columns=["ID", "Usuário"])

        # Exibir a lista de credenciais
        st.dataframe(df_credenciais)

        # Selecionar credencial para edição
        credencial_id = st.selectbox("Selecione o ID da credencial para editar:", df_credenciais["ID"])

        if credencial_id:
            # Consultar informações da credencial selecionada
            cursor.execute("SELECT * FROM credenciais WHERE id = %s", (credencial_id,))
            credencial = cursor.fetchone()

            # Formulário para editar informações da credencial
            usuario = st.text_input("Usuário", value=credencial[1])
            senha = st.text_input("Senha", value=credencial[2], type="password")

            if st.button("Salvar"):
                cursor.execute("UPDATE credenciais SET usuario = %s, senha = %s WHERE id = %s",
                               (usuario, senha, credencial_id))
                conn.commit()
                st.success("Credencial atualizada com sucesso!")

    elif menu == "Listar Acessos":
        st.subheader("Acessos dos Clientes")
        # Listar todos os clientes com LEFT JOIN para incluir clientes sem acessos

        cursor.execute(
            """
            SELECT c.id AS cliente_id, c.nome, ac.data_limite, ac.bypass 
            FROM clientes c 
            LEFT JOIN acesso_cliente ac ON ac.cliente_id = c.id
            """
        )
        acessos = cursor.fetchall()
        df_acessos = pd.DataFrame(acessos, columns=["ID do Cliente", "Nome", "Data Limite", "Bypass"])

        # Exibir a lista de acessos
        st.dataframe(df_acessos)

        # Selecionar um cliente para editar acesso
        cliente_edit = st.selectbox("Selecione o ID do Cliente para editar acesso:",
                                    df_acessos["ID do Cliente"].unique())

        # Verificar se o cliente já possui um acesso
        cursor.execute("SELECT * FROM acesso_cliente WHERE cliente_id = %s", (cliente_edit,))

        acesso_existente = cursor.fetchone()
        if acesso_existente:

            # Campos para edição
            nova_data_limite_edit = st.date_input("Nova Data Limite:",
                                                  value=acesso_existente[1])  # Assuming date is the second column

            novo_bypass_edit = st.number_input("Novo Valor do Bypass:", value=acesso_existente[2], min_value=0,
                                               max_value=1)  # Assuming bypass is the third column

            if st.button('Confirmar edição'):
                # Atualiza os dados de acesso
                cursor.execute(
                    "UPDATE acesso_cliente SET data_limite = %s, bypass = %s WHERE cliente_id = %s",
                    (nova_data_limite_edit, novo_bypass_edit, cliente_edit)
                )
                conn.commit()
                st.success("Acesso editado com sucesso!")
        else:
            st.warning("Nenhum acesso encontrado para este cliente.")

        # Fechar o cursor e a conexão
        cursor.close()
        conn.close()

def main():
    print(f'Logged_In Main: {controller.get('logged_in')}')
    print(f'Cliente Main: {controller.get('cliente_id')}')
    # Verifica se o usuário está logado
    logged_in = controller.get('logged_in')
    attempt_count = 0  # Contador de tentativas de login

    while logged_in is None:
        logged_in = controller.get('logged_in')
        attempt_count += 1

        # Pausa para evitar sobrecarga no processamento
        time.sleep(0.1)  # Aguarda 1 segundo antes de verificar novamente

        # Se o contador de tentativas bater 5, seta logged_in como False
        if attempt_count >= 5:
            controller.set('logged_in', False)
            controller.set('cliente_id', False)
            logged_in = False  # Sai do loop

        # Pausa para evitar sobrecarga no processamento
        time.sleep(1)

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
            # Trecho desabilitado por enquanto. Criar depois uma lógica de vendas integrada.
            # controller.set('logged_in', False)  # Redefine o estado de login
            # controller.set('cliente_id', False)
            # login(controller)
        else:
            main_page(controller)
    elif logged_in is False:
        if st.session_state['screen'] == 'login':
            login(controller)
        elif st.session_state['screen'] == 'criar_conta':
            criar_nova_conta()
        else:
            login(controller)
    else:
        if st.button('Primeiro login?'):
            controller.set('logged_in', False)
            st.rerun()
        st.image('logo_atualizada.png', use_column_width=True)


if __name__ == "__main__":
    print(f'Logged_In main=main: {controller.get('logged_in')}')
    print(f'Cliente main=main: {controller.get('cliente_id')}')
    main()
