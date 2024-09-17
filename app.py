import streamlit as st
import requests
import pandas as pd
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
from streamlit_cookies_controller import CookieController

# Configurações do layout e tema
st.set_page_config(page_title="IA BET", ) # layout="wide"

# Carregar a chave da API do OpenAI do arquivo .env
load_dotenv()
api_key_openai = os.getenv("OPENAI_API_KEY")
api_key_rapidapi = os.getenv("X-RAPIDAPI-KEY")

# Initialize the CookieController
controller = CookieController()
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

# Função para obter fixtures
def fetch_fixtures(date, league_id):
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
    headers = {
        'x-rapidapi-key': api_key_rapidapi,
        'x-rapidapi-host': "api-football-v1.p.rapidapi.com"
    }
    # Extraindo o ano da data escolhida para a temporada
    season = pd.to_datetime(date).year
    params = {"date": date, "league": league_id, "season": season}
    response = requests.get(url, headers=headers, params=params)
    fixtures_data = response.json()
    # print("Fixtures Data:", fixtures_data)  # Debug
    return fixtures_data.get('response', [])

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
                predictions)
    else:
        # Return default values if no data is available
        return 'N/A', 'N/A', 'No data available', 'No advice available', 'No data available', 'No data available', 'No advice available'

# Sidebar para configurações
st.sidebar.title("Configurações")

# Selecionar idioma
languages = ['Inglês', 'Espanhol', 'Chinês', 'Hindi', 'Árabe', 'Português', 'Bengali', 'Russo', 'Japonês', 'Lahnda',
             'Alemão', 'Francês', 'Coreano', 'Italiano', 'Turco', 'Vietnamita', 'Polonês', 'Ucraniano', 'Holandês', 'Grego']
selected_language = st.sidebar.selectbox("Selecione o idioma:", languages, index=languages.index(controller.get('language')))
controller.set('language', selected_language)

# Campo de entrada para nome do usuário
user_name = st.sidebar.text_input("Digite seu nome:", value=controller.get('user_name'))
controller.set('user_name', user_name)

# Converte o valor do cookie para float, se não for None
bet_temperature = float(controller.get('bet_temperature'))

# Configura o slider
bet_temperature = st.sidebar.slider(
    "Defina a temperatura da aposta (0 a 1):",
    min_value=0.0,
    max_value=1.0,
    value=bet_temperature,
    step=0.1,
    help="Quanto maior a temperatura, mais arriscada a bet."
)

# Adiciona HTML e CSS para os emojis
st.sidebar.markdown("""
    <style>
    .slider-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        position: relative;
        margin-top: -20px;
    }
    .slider-container div {
        font-size: 24px;
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

# Selecionar data
date = st.date_input("Selecione a data:", pd.to_datetime('today'), format="DD/MM/YYYY")

with st.spinner("Carregando países..."):
    countries = fetch_countries()

# Buscar países
if countries:
    country_names = [country['name'] for country in countries]

    # Selecionar o país armazenado, se disponível
    selected_country = st.selectbox("Selecione o país:", country_names, index=country_names.index(
        controller.get('selected_country')) if controller.get('selected_country') in country_names else 0)
    controller.set('selected_country', selected_country)

    # Buscar ligas para o país selecionado
    if selected_country:
        with st.spinner("Carregando ligas..."):
            leagues = fetch_leagues(selected_country)
        if leagues:
            league_names = [league['league']['name'] for league in leagues]

            # Selecionar a liga armazenada, se disponível
            selected_league = st.selectbox("Selecione a liga:", league_names, index=league_names.index(
                controller.get('selected_league')) if controller.get('selected_league') in league_names else 0)
            controller.set('selected_league', selected_league)

            if selected_league:
                league_id = next(
                    (league['league']['id'] for league in leagues if league['league']['name'] == selected_league), None)
                if league_id:
                    with st.spinner("Carregando jogos..."):
                        fixtures = fetch_fixtures(date, league_id)
                    if fixtures:
                        games = [
                            {
                                'game_info': f"{fixture['teams']['home']['name']} vs {fixture['teams']['away']['name']} - {fixture['fixture']['date']}",
                                'fixture_id': fixture['fixture']['id']
                            }
                            for fixture in fixtures
                        ]
                        game_options = [game['game_info'] for game in games]
                        selected_game_info = st.selectbox("Escolha um jogo:", game_options)

                        if selected_game_info:
                            fixture_id = next(
                                game['fixture_id'] for game in games if game['game_info'] == selected_game_info
                            )

                            # Adiciona um botão para calcular as previsões
                            if st.button("Calcular Previsão"):
                                (home_team_logo_url,
                                 away_team_logo_url,
                                 home_team_name,
                                 away_team_name,
                                 home_team_last_5_games,
                                 away_team_last_5_games,
                                 predictions) = get_prediction(fixture_id)

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

                                st.write("**Inteligência Artificial Calculando:**")

                                prompt = (
                                    f"""
                                    Sempre me chame pelo meu nome, mesmo que isso seja ridículo. Meu nome é: {user_name}
                                    Você é um especialista em apostas online, focado em oferecer a melhor dica baseada no conteúdo de um JSON fornecido. 
                                    Sempre responda de forma confiante, como alguém com grande experiência em bets, e adapte sua resposta ao que está no JSON. 
                                    Lembre-se de que quem está lendo já entende de apostas, então evite ser excessivamente cauteloso ou explicar demais. 
                                    O ambiente é descontraído, e seu papel é destacar a aposta contida no JSON (mas não mencione que o resultado vem de um json.
                                    Responda como se voce tivesse calculado e obtido uma aposta sólida, como resultado de inteligência artificial). 
                                    Abaixo responda com uma tabela com a equipe e na frente a aposta. 
                                    Sempre responda em {selected_language}, e adicione as estatísticas à tabela gerada. Seja profissional.
                                    Agora, com base no seguinte JSON, dê sua dica:
                                    {str(predictions)}
                                    Utilize essas estatísticas adicionais para montar a resposta.
                                    Não é necessário adicionar os dados à tabela, somente ao texto de resposta.
                                    (considere W - Vitória, D - Empate, L - Perda):
                                    Últimos 5 jogos da casa: {home_team_last_5_results}
                                    Últimos 5 jogos do visitante: {away_team_last_5_results}
                                    Temperatura da aposta:
                                    - Considere que 0 é instrução para ser extremamente seguro, e 1 extremamente arriscado.
                                    Temperatura escolhida: {bet_temperature}
                                    """
                                )

                                llm = ChatOpenAI(model_name="gpt-4o-mini", openai_api_key=api_key_openai)

                                # Cria a chain para lidar com o LLM
                                chain = llm.invoke(prompt)

                                response = chain.content
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
