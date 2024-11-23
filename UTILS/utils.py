import base64
from PIL import Image, ImageDraw
import os
from dotenv import load_dotenv
import requests
import pandas as pd
from datetime import datetime
import mysql.connector
from UTILS.connection import get_connection


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


def stats_to_dataframe(st, team_stats, team_name):
    with st.spinner("Carregando estatísticas"):
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
            with st.expander(f"Estatísticas de {team_name}", expanded=False):
                st.table(df.style.set_properties(**{'text-align': 'center'}))

            return df
        else:
            st.write(f"Estatísticas para {team_name} não disponíveis.")


def registrar_consumo(cliente_id, valor_consumo, configuracao_consumo):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Data e hora atuais
        datahora = datetime.now()

        # Inserir um novo registro na tabela de consumos
        cursor.execute(
            "INSERT INTO consumos (cliente_id, datahora, valor_consumo, configuracao_consumo) VALUES (%s, %s, %s, %s)",
            (cliente_id, datahora, valor_consumo, configuracao_consumo)
        )

        conn.commit()  # Confirma a transação
        print("Consumo registrado com sucesso.")

    except mysql.connector.Error as err:
        print(f"Erro ao registrar consumo: {err}")

    finally:
        # Fechar cursor
        cursor.close()


def calcular_saldo(cliente_id, conn):
    saldo = 0.0  # Inicializa o saldo

    cursor = conn.cursor()

    # Somar os valores das compras
    cursor.execute("SELECT SUM(valor_compra) FROM compras_creditos WHERE cliente_id = %s", (cliente_id,))
    valor_compras = cursor.fetchone()[0]  # Obtém o valor total de compras
    if valor_compras is not None:
        saldo += float(valor_compras)  # Converte para float antes de somar

    # Subtrair os valores dos consumos
    cursor.execute("SELECT SUM(valor_consumo) FROM consumos WHERE cliente_id = %s", (cliente_id,))
    valor_consumos = cursor.fetchone()[0]  # Obtém o valor total de consumos
    if valor_consumos is not None:
        saldo -= float(valor_consumos)  # Converte para float antes de subtrair

    conn.close()  # Fecha a conexão
    return saldo if saldo > 0 else 0


def verificar_cookies(controller):
    # Tenta obter os valores da session state, e caso não existam, ele inicializa como False
    cliente_id = controller.get("cliente_id")
    logged_in = controller.get("logged_in")
    # print(f'Retornando o client id e o logged in como {cliente_id, logged_in} na pagina: {pagina}')
    return cliente_id, logged_in


def verificar_trial(cliente_id):
    # Estabelecer a conexão com o banco de dados
    conn = get_connection()
    cursor = conn.cursor()

    # Executar a query para buscar o trial credits
    cursor.execute('SELECT trial_credits FROM acesso_cliente WHERE cliente_id = %s', (cliente_id,))

    # Obter o resultado da consulta
    trial_credits = cursor.fetchone()

    # Fechar o cursor e a conexão
    cursor.close()
    conn.close()

    # Validar se um resultado foi encontrado
    if trial_credits:
        trial_credits = trial_credits[0]  # Acessar o primeiro item da tupla
        print(f'Trial credits obtido para o cliente {cliente_id}: {trial_credits}')
    else:
        trial_credits = 0  # Definir um valor padrão, se não houver resultado
        print(f'Nenhum trial credits encontrado para o cliente {cliente_id}. Retornando 0.')
    return trial_credits


def recarga_inicial(st, cliente_id, valor):
    conn = get_connection()
    cursor = conn.cursor()

    # Consultar o saldo total atual do cliente
    cursor.execute('''
        SELECT SUM(valor_compra) 
        FROM compras_creditos 
        WHERE cliente_id = %s
    ''', (cliente_id,))
    saldo_atual = cursor.fetchone()[0] or 0  # Se for None, atribui 0

    # Adicionar 1 dólar na tabela de compras de créditos
    cursor.execute('''
        INSERT INTO compras_creditos (cliente_id, datahora, valor_compra)
        VALUES (%s, %s, %s)
    ''', (cliente_id, datetime.now(), valor))

    # Atualizar trial_credits para 1
    cursor.execute('UPDATE acesso_cliente SET trial_credits = 1 WHERE cliente_id = %s', (cliente_id,))

    # Salvar as mudanças
    conn.commit()

    # Fechar conexão
    cursor.close()
    conn.close()

    # Exibir mensagem de sucesso com o saldo atualizado
    novo_saldo = saldo_atual + 1
    st.success(f"Recarga inicial realizada com sucesso! Saldo atual: ${novo_saldo:.2f}")


def get_llm(model_name, temperature):
    from langchain_openai import ChatOpenAI
    from langchain_google_genai import ChatGoogleGenerativeAI
    import google.generativeai as genai

    # Configure Generative AI with API key
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

    if model_name == "gemini-1.5-flash" or model_name == "Gemini 1.5 Flash":
        return ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=temperature)
    elif model_name == "gemini-1.5-pro" or model_name == "Gemini 1.5 Pro":
        return ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=temperature)
    elif model_name == "gemini-pro" or model_name == "Gemini Pro":
        return ChatGoogleGenerativeAI(model="gemini-pro", temperature=temperature)
    elif model_name == "gpt-3.5-turbo" or model_name == "GPT-3.5 Turbo":
        return ChatOpenAI(model="gpt-3.5-turbo", temperature=temperature)
    elif model_name == "gpt-4o-mini" or model_name == "GPT-4o Mini":
        return ChatOpenAI(model="gpt-4o-mini", temperature=temperature)
    elif model_name == "gpt-4o" or model_name == "GPT-4o":
        return ChatOpenAI(model="gpt-4o", temperature=temperature)


def get_prediction(fixture_id, custo_consulta, cliente_id, configuracao_consumo):
    # Registrar o consumo
    registrar_consumo(cliente_id, custo_consulta, configuracao_consumo)

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


# Função para obter a cotação do dólar
def obter_cotacao_dolar(st):
    url = "https://economia.awesomeapi.com.br/json/last/USD-BRL"
    try:
        response = requests.get(url)
        response.raise_for_status()
        dados = response.json()
        cotacao = float(dados["USDBRL"]["bid"])
        return cotacao
    except requests.RequestException as e:
        st.error(f"Erro ao obter cotação do dólar: {str(e)}")
        return None
