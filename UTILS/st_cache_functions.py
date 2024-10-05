import streamlit as st
from dotenv import load_dotenv
import os
import requests
import pandas as pd



# Carregar a chave da API do OpenAI do arquivo .env
load_dotenv()
api_key_openai = os.getenv("OPENAI_API_KEY")
api_key_rapidapi = os.getenv("X-RAPIDAPI-KEY")


# Configurar a chave da API e a URL
url = "https://api-football-v1.p.rapidapi.com/v3/odds"
headers = {
    "x-rapidapi-key": api_key_rapidapi,
    "x-rapidapi-host": "api-football-v1.p.rapidapi.com"
}

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
    season = pd.to_datetime(date).year
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