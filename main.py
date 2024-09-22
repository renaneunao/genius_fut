from streamlit_cookies_controller import CookieController
import streamlit as st
import requests
import pandas as pd
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
import sqlite3
from datetime import datetime

def criar_tabelas():
    # Conecte-se aos bancos de dados usando os caminhos absolutos
    conn_credenciais = sqlite3.connect('credenciais.db')
    conn_clientes = sqlite3.connect('clientes.db')
    conn_acesso = sqlite3.connect('acesso_cliente.db')

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
    conn_credenciais = sqlite3.connect('credenciais.db')
    conn_clientes = sqlite3.connect('clientes.db')

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
    conn = sqlite3.connect('credenciais.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM credenciais WHERE usuario = ? AND senha = ?', (usuario, senha))
    data = cursor.fetchone()
    conn.close()

    return data  # Retorna apenas o id


def verificar_acesso(cliente_id):
    conn = sqlite3.connect('acesso_cliente.db')
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
            conn_clientes = sqlite3.connect('clientes.db')
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


def main_page(controller):
    st.title("Tela Principal")
    controller.set('logged_in', True)
    if 'cliente_id' in st.session_state:
        # Conecte-se ao banco de dados usando o caminho absoluto
        conn_clientes = sqlite3.connect('clientes.db')
        cursor = conn_clientes.cursor()

        cliente_id = st.session_state.cliente_id

        cursor.execute("SELECT nome FROM clientes WHERE id = ?", (cliente_id,))
        cliente = cursor.fetchone()

        if cliente:  # Verifica se o cliente não é None
            nome_cliente = cliente[0]
            st.write(f"Bem-vindo, {nome_cliente}!")
        else:
            nome_cliente = ''
            st.write("Cliente não encontrado.")

        conn_clientes.close()

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

        # Sidebar para timezone e botão de sair
        st.sidebar.write(f"Horários de {default_timezone}")

        # Criar um layout de colunas para o botão de sair e trocar timezone
        col1, col2 = st.sidebar.columns(2)

        # Adiciona o botão para trocar timezone
        with col1:
            if st.button("Trocar timezone"):
                selected_timezone = st.selectbox("Selecione o timezone:", timezones,
                                                 index=timezones.index(default_timezone))
            else:
                selected_timezone = default_timezone

        # Adiciona o botão de sair
        with col2:
            if st.button("Sair da conta"):
                # Remover ou setar como falso o cookie de logged_in
                controller.set('logged_in', False)  # Remover o estado de login
                controller.set('cliente_id', '')  # Opcional: limpar o cliente_id
                # Verifica se o usuário está logado
                logged_in = controller.get('logged_in')

                print(f'App: O logged_in é: {logged_in}')

                # Redirecionar para a página de login
                st.success("Você saiu da conta.")
                st.rerun()

        date = st.sidebar.date_input("Selecione a data:", pd.to_datetime('today'), format="DD/MM/YYYY")

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

        # Interface com Streamlit
        st.title('Análise de Confrontos de Futebol')

        with st.spinner("Carregando países..."):
            countries = fetch_countries()

        # Buscar países
        if countries:
            country_names = [country['name'] for country in countries]

            # Selecionar o país armazenado, se disponível
            selected_country = st.sidebar.selectbox("Selecione o país:", country_names, index=country_names.index(
                controller.get('selected_country')) if controller.get('selected_country') in country_names else 0)
            controller.set('selected_country', selected_country)

            # Buscar ligas para o país selecionado
            if selected_country:
                with st.spinner("Carregando ligas..."):
                    leagues = fetch_leagues(selected_country)
                if leagues:
                    league_names = [league['league']['name'] for league in leagues]

                    # Selecionar a liga armazenada, se disponível
                    selected_league = st.sidebar.selectbox("Selecione a liga:", league_names, index=league_names.index(
                        controller.get('selected_league')) if controller.get('selected_league') in league_names else 0)
                    controller.set('selected_league', selected_league)

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
                                selected_game_info = st.sidebar.selectbox("Escolha um jogo:", game_options)

                                if selected_game_info:
                                    fixture_id = next(
                                        game['fixture_id'] for game in games if game['game_info'] == selected_game_info
                                    )

                                    # Adiciona um botão para calcular as previsões
                                    if st.sidebar.button("Calcular Previsão"):
                                        (home_team_logo_url,
                                         away_team_logo_url,
                                         home_team_name,
                                         away_team_name,
                                         home_team_last_5_games,
                                         away_team_last_5_games,
                                         predictions,
                                         team_id_home,
                                         team_id_away) = get_prediction(fixture_id)

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

                                        # Exibir estatísticas na interface
                                        st.title("Análise de Desempenho - Estatísticas de Futebol")

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
                                            - Abaixo, apresente uma tabela com as equipes e, ao lado, as respectivas apostas.

                                              | Time             | Aposta                  |
                                              |------------------|------------------------|
                                              | Casa: `{home_team_name}`  | `sua_dica_para_a_aposta` |
                                              | Visitante: `{away_team_name}` | `sua_dica_para_a_aposta` |

                                            - Com base no seguinte JSON, forneça sua dica:
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
                                            - Forneça pelo menos uma sugestão adicional de aposta. Se a temperatura for acima 
                                            da média, ofereça opções mais arriscadas com base nas estatísticas. Apresente essas 
                                            apostas em uma tabela separada, numerada. 
                                            - Para sugestões de under/over gols, mencione o jogo se for geral e o time 
                                            específico se for uma aposta focada.

                                              Exemplos de sugestões com base na temperatura:
                                              - Temperatura 0: uma sugestão bastante segura.
                                              - Temperatura 0.5: uma ou duas sugestões.
                                              - Temperatura 1: três ou mais sugestões.

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
                                st.write("Nenhum jogo encontrado para a data e liga selecionadas.")
                        else:
                            st.write("ID da liga não encontrado.")
                    else:
                        st.write("Nenhuma liga encontrada para o país selecionado.")
                else:
                    st.write("Nenhuma liga encontrada para o país selecionado.")
        else:
            st.write("Nenhum país encontrado.")
    else:
        st.write("Você não está logado.")


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
    else:
        if st.button('Primeiro login?'):
            controller.set('logged_in', False)
            st.rerun()

if __name__ == "__main__":
    main()
