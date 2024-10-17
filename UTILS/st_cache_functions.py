import streamlit as st
from dotenv import load_dotenv
import os
import requests
import pandas as pd
import json

# Definir o diretório onde os arquivos JSON serão armazenados
CACHE_DIR = "consultas_pre_carregadas"

# Certificar-se de que o diretório existe
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)


# Função para salvar dados em um arquivo JSON
def save_to_json(data, filename):
    with open(os.path.join(CACHE_DIR, filename), 'w') as f:
        json.dump(data, f)


# Função para carregar dados de um arquivo JSON
def load_from_json(filename):
    filepath = os.path.join(CACHE_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return json.load(f)
    return None


# Carregar a chave da API do OpenAI do arquivo .env
load_dotenv()
api_key_openai = os.getenv("OPENAI_API_KEY")
api_key_rapidapi = os.getenv("X-RAPIDAPI-KEY")

# Configurar a chave da API e a URL
url = "https://api-football-v1.p.rapidapi.com/v2/odds"
headers = {
    "x-rapidapi-key": api_key_rapidapi,
    "x-rapidapi-host": "api-football-v1.p.rapidapi.com"
}


@st.cache_data
def fetch_timezones():
    filename = "timezones.json"

    # Tentar carregar os dados do cache (arquivo JSON)
    cached_data = load_from_json(filename)
    if cached_data:
        print('Carregado o timezone da cache')
        return cached_data

    # Caso não exista, faz a requisição à API
    url = "https://api-football-v1.p.rapidapi.com/v3/timezone"
    headers = {
        'x-rapidapi-key': api_key_rapidapi,
        'x-rapidapi-host': "api-football-v1.p.rapidapi.com"
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        timezones_data = response.json().get('response', [])
        save_to_json(timezones_data, filename)  # Salvar os dados no arquivo JSON
        return timezones_data
    else:
        st.error("Erro ao buscar timezones.")
        return []


@st.cache_data
def fetch_countries():
    filename = "countries.json"

    # Tentar carregar os dados do cache (arquivo JSON)
    cached_data = load_from_json(filename)
    if cached_data:
        print('Carregados os paises na cache')
        return cached_data

    # Caso não exista, faz a requisição à API
    url = "https://api-football-v1.p.rapidapi.com/v3/countries"
    headers = {
        'x-rapidapi-key': api_key_rapidapi,
        'x-rapidapi-host': "api-football-v1.p.rapidapi.com"
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        countries_data = response.json().get('response', [])
        save_to_json(countries_data, filename)  # Salvar os dados no arquivo JSON
        return countries_data
    else:
        st.error("Erro ao buscar países.")
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


@st.cache_data
def get_bookmakers():
    filename = "bookmakers.json"

    # Tentar carregar os dados do cache (arquivo JSON)
    cached_data = load_from_json(filename)
    if cached_data:
        print('Carregados os bookmakers na cache')
        return cached_data

    # Caso não exista, faz a requisição à API
    url = "https://api-football-v1.p.rapidapi.com/v3/odds/bookmakers"
    headers = {
        "x-rapidapi-key": api_key_rapidapi,
        "x-rapidapi-host": "api-football-v1.p.rapidapi.com"
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        bookmakers_data = [bookmaker["name"] for bookmaker in response.json().get("response", [])]
        save_to_json(bookmakers_data, filename)  # Salvar os dados no arquivo JSON
        return bookmakers_data
    else:
        st.error("Erro ao buscar casas de apostas.")
        return []


@st.cache_data  # Cache para armazenar odds
def fetch_odds(fixture_id):
    url = "https://api-football-v1.p.rapidapi.com/v3/odds"

    querystring = {"fixture": fixture_id}

    headers = {
        "x-rapidapi-key": api_key_rapidapi,
        "x-rapidapi-host": "api-football-v1.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

    if response.status_code == 200:
        return response.json()
    else:
        st.error("Erro ao buscar odds. Verifique o ID do fixture.")
        return None