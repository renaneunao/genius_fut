import base64
from PIL import Image, ImageDraw
import os
from dotenv import load_dotenv
import requests
import pandas as pd

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

def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        encoded_string = base64.b64encode(img_file.read()).decode()
    return encoded_string


def get_prediction(fixture_id):
    # Carregar a chave da API do OpenAI do arquivo .env
    load_dotenv()
    api_key_rapidapi = os.getenv("X-RAPIDAPI-KEY")
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


def stats_to_dataframe(st, team_stats, team_name):
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