import requests
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
import os

# Carregar as chaves da API
load_dotenv()
api_key_rapidapi = os.getenv("X-RAPIDAPI-KEY")


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


# Função para converter estatísticas em DataFrame
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
        df["Média de Gols Marcados"] = df["Gols Marcados"] / df["Jogos"]
        df["Média de Gols Sofridos"] = df["Gols Sofridos"] / df["Jogos"]

        # Exibir o DataFrame no Streamlit
        st.subheader(f"Estatísticas de {team_name}")
        st.dataframe(df)
        return df
    else:
        st.write(f"Estatísticas para {team_name} não disponíveis.")


# Exemplo de uso para um time
season = "2023"  # Temporada desejada
team_id_home = 33  # ID do time da casa
team_id_away = 34  # ID do time visitante

# Obter estatísticas para os dois times
home_team_stats = fetch_team_stats(season, team_id_home)
away_team_stats = fetch_team_stats(season, team_id_away)

# Exibir estatísticas na interface
st.title("Análise de Desempenho - Estatísticas de Futebol")

# Converter estatísticas em DataFrame e exibir
stats_to_dataframe(home_team_stats, "Time da Casa")
stats_to_dataframe(away_team_stats, "Time Visitante")
