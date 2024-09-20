import streamlit as st
import requests
import pandas as pd
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
from streamlit_cookies_controller import CookieController
import pytz
from datetime import datetime

# Configurações do layout e tema
st.set_page_config(page_title="IA BET", ) # layout="wide"

# Carregar a chave da API do OpenAI do arquivo .env
load_dotenv()
api_key_openai = os.getenv("OPENAI_API_KEY")
api_key_rapidapi = os.getenv("X-RAPIDAPI-KEY")

# Initialize the CookieController
controller = CookieController()

# Função para converter o horário do jogo para o fuso horário selecionado
def convert_timezone(fixture_date, timezone):
    utc_time = pd.to_datetime(fixture_date).tz_localize('UTC')
    local_time = utc_time.astimezone(pytz.timezone(timezone))
    return local_time

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

# Função para obter fixtures
# Função para obter fixtures de acordo com a data, liga e timezone
def fetch_fixtures(date, league_id, timezone):
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
    headers = {
        'x-rapidapi-key': api_key_rapidapi,
        'x-rapidapi-host': "api-football-v1.p.rapidapi.com"
    }
    # Extraindo o ano da data escolhida para a temporada
    season = pd.to_datetime(date).year
    params = {
        "date": date,
        "league": league_id,
        "season": season,
        "timezone": timezone  # Utiliza o timezone selecionado
    }
    response = requests.get(url, headers=headers, params=params)
    fixtures_data = response.json()
    return fixtures_data.get('response', [])

# Sidebar para timezone
timezones = fetch_timezones()

selected_timezone = st.sidebar.selectbox("Selecione o timezone:", timezones, index=timezones.index("America/Sao_Paulo"))  # Define "America/Sao_Paulo" como padrão
# Selecionar data
date = st.sidebar.date_input("Selecione a data:", pd.to_datetime('today'), format="DD/MM/YYYY")

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
with st.sidebar.expander("Configurações Gerais"):
    st.title("Configurações Gerais")
    # Lista de idiomas
    languages = ['Inglês', 'Espanhol', 'Chinês', 'Hindi', 'Árabe', 'Português', 'Bengali', 'Russo', 'Japonês', 'Lahnda',
                 'Alemão', 'Francês', 'Coreano', 'Italiano', 'Turco', 'Vietnamita', 'Polonês', 'Ucraniano', 'Holandês', 'Grego']

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
    user_name = st.text_input("Digite seu nome:", value=controller.get('user_name'))
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
            league_logos = [league['league']['logo'] for league in leagues]

            # Container para as logos das ligas
            cols = st.sidebar.columns(len(league_logos))
            selected_league_id = None

            for i, logo_url in enumerate(league_logos):
                with cols[i]:
                    if st.sidebar.button("", key=i):
                        selected_league_id = leagues[i]['league']['id']
                    st.sidebar.image(logo_url, width=40)
            controller.set('selected_league', selected_league_id)

            if selected_league_id and date:
                with st.spinner("Carregando jogos..."):
                    fixtures = fetch_fixtures(date, selected_league_id, selected_timezone)
                if fixtures:
                    games = [
                        {
                            'game_info': f"{fixture['teams']['home']['name']} vs {fixture['teams']['away']['name']} - {fixture['fixture']['date']}",
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
                                1. Sempre responda em {selected_language}
                                2. Sempre me chame pelo meu nome. Meu nome é: {user_name}.
                                3. Você é um especialista em apostas online, com foco em fornecer a melhor dica com 
                                base nas informações de um JSON fornecido. 
                                4. Responda com confiança, como um profissional experiente em apostas, e alinhe sua 
                                resposta com o conteúdo do JSON.
                                5. O ambiente é descontraído e seu papel é destacar a aposta contida no JSON, sem 
                                mencionar que a informação vem de um JSON.
                                6. Responda como se tivesse calculado uma aposta sólida, como resultado de inteligência 
                                artificial e inclua as estatísticas na tabela gerada. Mostre na tabela apenas a
                                equipe que for mencionada na aposta principal.
                                7. Abaixo, apresente uma tabela com a equipe e, ao lado, a aposta.
                                Casa: {home_team_name}, Visitante: {away_team_name}.
                                Com base no seguinte JSON, forneça sua dica:
                                {str(predictions)}
                                8. Utilize as estatísticas adicionais para compor a resposta, sem adicionar dados à 
                                tabela, apenas no texto.
                                (Considere W - Vitória, D - Empate, L - Perda):
                                Últimos 5 jogos da casa: {home_team_last_5_results}.
                                Últimos 5 jogos do visitante: {away_team_last_5_results}.
                                9. Temperatura da aposta:
                                - Considere que 0 indica extrema segurança e 1, extrema risco.
                                Temperatura escolhida: {bet_temperature}.
                                10. Além da aposta principal sugerida, se a temperatura estiver acima da média, 
                                ofereça opções adicionais mais arriscadas baseadas nas estatísticas de gols do JSON, 
                                sem mencionar a temperatura. Essas apostas adicionais devem estar em uma tabela 
                                separada, numerada. Se for uma sugestão de under/over gols para o jogo, mencione o jogo. 
                                se for uma sugestão de under/over gols para um time específico, mencione o time.
                                Temperatura 0, nenhuma sugestão extra. Temperatura em 0.5, uma ou duas sugestões.
                                Temperatua em 1, 3 ou mais sugestões.
                                11. Se o json mostra uma tendencia under gols, não sugira over.
                                Se o json mostra uma tendencia over gols, não sugira under.
                                12. Se a temperatura estiver muito alta, pode ousar nas sugestões, inclusive se a tendencia 
                                over gols, pode incrementar o over, e o mesmo para under. Exemplo:
                                se a tendência for under: -3.5 (tendência) -> tip: -2.5 gols.
                                se a tendência for over: +2.5 gols (tendência) -> tip +3,5 gols.
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
