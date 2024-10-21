from datetime import datetime
import pytz
import pandas as pd
import streamlit as st
from streamlit_cookies_controller import CookieController, RemoveEmptyElementContainer
import time

from UTILS.utils import (get_prediction,
                         stats_to_dataframe,
                         calcular_saldo,
                         get_llm,
                         verificar_cookies)
from UTILS.connection import get_connection
from UTILS.st_cache_functions import (fetch_timezones,
                                      fetch_countries,
                                      fetch_fixtures,
                                      fetch_leagues,
                                      fetch_team_stats,
                                      get_bookmakers,
                                      fetch_odds)
from UTILS.listas_bets import bets_obrigatorias, bets_gols, bets_cartoes, bets_escanteios, bet_marcadores, bets_finalizadores
from UTILS.lista_languages import languages
from UTILS.prompt_response import get_prompt

from streamlit_extras.colored_header import colored_header
from streamlit_extras.bottom_container import bottom
from streamlit_extras.grid import grid
from streamlit_vertical_slider import vertical_slider

# Configuração da página
st.set_page_config(page_title="GeniusFut", page_icon="icone_mini.png")

administrador = 3


# Inicializa o controlador de cookies
controller = CookieController(key='cookies')
RemoveEmptyElementContainer()

# CSS customizado para ocultar elementos e ajustar estilo
st.markdown(
    r"""
    <style>
    /* Oculta o botão Deploy */
    #root > div:nth-child(1) > div.withScreencast > div > div > header > div.st-emotion-cache-15ecox0.ezrtsby0 > div.stAppDeployButton {
        display: none;
    }
    /* Remove margens e padding adicionais do aplicativo */
    .stApp {
        margin: 0;
        padding: 0;
    }
    /* Bloquear o redimensionamento da sidebar */
    [data-testid="stSidebar"] {
        min-width: 250px;
        max-width: 250px;
        width: 250px;
    }
    /* Ajusta o tamanho da fonte a todos os <p> */
    div > label > div > div > div > p {
        font-size: 12px;
        white-space: nowrap;
    }
    /* Ajusta a altura do bottom container */
    div > div > div > div > div > div > details > div {
        height: 80px;
        overflow: hidden;
    }
    /* Ajusta a altura do bottom container */
    [data-testid="stBottomBlockContainer"] {
        height: 50px;
        padding: 0;
    }
    /* Estilo do expander */
    div > div > div > div > div > div > details > summary {
        background-color: #39FF14;
        color: black;
        font-weight: bold;
        padding: 5px;
        border-radius: 8px;
    }
    /* Estilo para o botão */
    .stButton {
        padding-top: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True
)


selected_country = None
selected_league = None
fixture_id = None
home_team_name = None
away_team_name = None
predictions = None
home_team_logo_url = None
away_team_logo_url = None
selected_game_info = None

# Controle de precificação
preco_bet_vitorias = 0.01
preco_bet_gols = 0.01
preco_bet_cantos = 0.015
preco_bet_marcador = 0.01
preco_bet_cartoes = 0.1
preco_bet_finalizacao = 0.015

preco_llm_gemini_1_5_flash = 0.06
preco_llm_gemini_1_5_pro = 0.08
preco_llm_gemini_pro = 0.10
preco_llm_gpt_3_5_turbo = 0.06  # para entrada
preco_llm_gpt_4o_mini = 0.08
preco_llm_gpt_4o = 0.15

preco_temperatura = 0.005
preco_odd_min = 0.005

preco_inicial = 0

# Exibir a imagem na sidebar
st.sidebar.image('logo_atualizada.png', use_column_width=True)

# Verifica os cookies e exibe os valores
cliente_id, logged_in = verificar_cookies(controller)

if cliente_id:
    conn = get_connection()
    cursor = conn.cursor()

    # Usar %s como placeholder no MySQL
    cursor.execute("SELECT nome FROM clientes WHERE id = %s", (cliente_id,))
    cliente = cursor.fetchone()
    saldo = calcular_saldo(cliente_id, conn)  # Chama a função para calcular o saldo
    conn.close()

    nome_cliente = cliente[0]
    colored_header(
        label=f"Bem-vindo, {nome_cliente}!",
        description=f"Aqui o GREEN é certo! Saldo Atual: ${saldo}",
        color_name="green-70",
    )

    timezones = fetch_timezones()
    default_timezone = "America/Sao_Paulo"
    selected_timezone = default_timezone
    timezone = pytz.timezone(selected_timezone)

    # Selecionar a data do jogo
    today = datetime.now(timezone).date()
    date = st.sidebar.date_input(
        "Selecione a data do jogo:",
        today,
        min_value=today,  # opcional: define a data mínima como hoje
        format="DD/MM/YYYY"
    )

    season = pd.to_datetime(date).year

    # Criando uma lista de LLMs com seus respectivos preços
    llms = {
        "Gemini 1.5 Flash": preco_llm_gemini_1_5_flash,
        "Gemini 1.5 Pro": preco_llm_gemini_1_5_pro,
        "Gemini Pro": preco_llm_gemini_pro,
        "GPT-3.5 Turbo": preco_llm_gpt_3_5_turbo,
        "GPT-4o Mini": preco_llm_gpt_4o_mini,
        "GPT-4o": preco_llm_gpt_4o,
    }

    selected_llm = st.sidebar.selectbox(
        "Selecione o cérbro do 🤖:",
        options=list(llms.keys())
    )

    preco_inicial += llms[selected_llm]

    col1, col2 = st.sidebar.columns(2)

    # Criar expander para opções 1, 2 e 3 na primeira coluna
    with col1:
        opcao1 = st.checkbox("Vitória", value=True)
        opcao2 = st.checkbox("Gols")
        opcao3 = st.checkbox("Cartões")

        bet_temperature = vertical_slider(
            key="temperatura",
            default_value=0,  # Representa 0.5 na escala de 0 a 100
            height=100,
            step=0.1,
            min_value=0,
            max_value=1,
            track_color="green",
            thumb_color="white",  # Bolinha
            slider_color=('red', 'white'),
            label="Temp",
        )

        controller.set("bet_temperature", bet_temperature)
    preco_inicial += (bet_temperature * preco_temperatura)

    # Criar expander para opções 4, 5 e 6 na segunda coluna
    with col2:
        opcao4 = st.checkbox("Cantos")
        opcao5 = st.checkbox("Marcador")
        opcao6 = st.checkbox("Finalização")

        min_odd = vertical_slider(
            key="odd_minima",
            default_value=1.1,  # Representa 1.1 na escala de 1.1 a 15
            height=100,
            step=0.1,
            min_value=1.1,
            max_value=15,  # Representa até 15.0
            track_color="green",
            thumb_color="blue",  # Bolinha
            slider_color=('blue', 'white'),
            label="Odd Mín.",
        )

        preco_inicial += (min_odd * preco_odd_min)

        # Armazena o valor da odd mínima no controller
        controller.set('min_odd_value', min_odd)

    # Mapeamento de grupos de bets
    bet_groups = {
        "Vitória": bets_obrigatorias,
        "Gols": bets_gols,
        "Cartões": bets_cartoes,
        "Cantos": bets_escanteios,
        "Marcador": bet_marcadores,
        "Finalização": bets_finalizadores,
    }

    # Limitar seleção com base no status
    bookmakers_list = get_bookmakers()
    max_selecoes = 3  # Até 3 opções para usuários
    label_casas = f"Selecione até {max_selecoes} casa(s) de aposta:"
    help_casas_aposta = "Você pode selecionar até 3 casas de aposta."

    # Multiselect para escolher casas de apostas
    selected_bookmakers = st.sidebar.multiselect(
        label_casas,
        options=bookmakers_list,
        max_selections=max_selecoes,
        default=bookmakers_list[7],
        help=help_casas_aposta,
        # disabled=not premium
    )

    # Verificar se pelo menos uma opção foi selecionada em cada grupo
    erro = False
    if not any([opcao1, opcao2, opcao3, opcao4, opcao5, opcao6]):
        st.sidebar.warning("Você deve selecionar pelo menos uma opção de Tipo de Aposta.")
        erro = True
    if not selected_bookmakers:  # Esta condição verifica se a lista está vazia
        st.sidebar.warning("Você deve selecionar pelo menos uma opção de Casa de Aposta.")
        erro = True

    selected_bets = []
    selected_bets_favoritas = []
    if opcao1:
        selected_bets.append("Vitória")
        selected_bets_favoritas.append("Vitória")
        preco_inicial += preco_bet_vitorias
    if opcao2:
        selected_bets.append("Gols")
        selected_bets_favoritas.append("Gols")
        preco_inicial += preco_bet_gols
    if opcao3:
        selected_bets.append("Cartões")
        selected_bets_favoritas.append("Cartões")
        preco_inicial += preco_bet_cartoes
    if opcao4:
        selected_bets.append("Cantos")
        selected_bets_favoritas.append("Cantos")
        preco_inicial += preco_bet_cantos
    if opcao5:
        selected_bets.append("Marcador")
        selected_bets_favoritas.append("Marcador")
        preco_inicial += preco_bet_marcador
    if opcao6:
        selected_bets.append("Finalização")
        selected_bets_favoritas.append("Finalização")
        preco_inicial += preco_bet_finalizacao

    for group in selected_bets:
        if group in bet_groups:
            selected_bets.extend(bet_groups[group])

    # Valores de precificação das casas de apostas
    preco_casas_aposta = {
        '10Bet': 0.03,
        'Marathonbet': 0.03,
        'Betfair': 0.05,
        'Pinnacle': 0.03,
        'SBO': 0.03,
        'Bwin': 0.03,
        'William Hill': 0.03,
        'Bet365': 0.06,
        'Dafabet': 0.03,
        'Ladbrokes': 0.03,
        '1xBet': 0.03,
        'BetFred': 0.03,
        '188Bet': 0.03,
        'Interwetten': 0.03,
        'Unibet': 0.03,
        '5Dimes': 0.03,
        'Intertops': 0.03,
        'Bovada': 0.03,
        'Betcris': 0.03,
        '888Sport': 0.03,
        'Tipico': 0.03,
        'Sportingbet': 0.05,
        'Betway': 0.03,
        'Expekt': 0.03,
        'Betsson': 0.03,
        'NordicBet': 0.03,
        'ComeOn': 0.03,
        'Netbet': 0.03,
        'Betano': 0.06,
        'Fonbet': 0.03
    }

    # Inicializar o preço total das casas de apostas
    preco_casas_selecionadas = 0

    # Iterar sobre as casas de apostas selecionadas e somar o preço correspondente
    for casa in selected_bookmakers:
        if casa in preco_casas_aposta:
            preco_casas_selecionadas += preco_casas_aposta[casa]

    # Somar o preço das casas de apostas ao preço total inicial
    preco_inicial += preco_casas_selecionadas

    st.sidebar.write(f'Preco da busca: {preco_inicial}')

    # Campo de entrada para nome do usuário
    user_name_cookie = controller.get('user_name')
    user_name = st.sidebar.text_input("Digite seu nome:", value=user_name_cookie)
    controller.set('user_name', user_name)

    # Obter o idioma selecionado do cookie ou usar o primeiro idioma da lista como padrão
    selected_language_cookie = controller.get('language')
    if selected_language_cookie in languages:
        selected_language = selected_language_cookie
    else:
        selected_language = languages[5]  # Defina um valor padrão, por exemplo, o primeiro idioma da lista

    # Seleção do idioma na sidebar
    with st.sidebar.expander(selected_language, expanded=False):
        selected_language = st.selectbox("Selecione o idioma:", languages, index=languages.index(selected_language))
        controller.set('language', selected_language)

    # Cria um expander para o timezone
    with st.sidebar.expander(default_timezone, expanded=False):
        # Dropdown para selecionar o timezone
        selected_timezone = st.selectbox("Selecione o timezone:", timezones,
                                         index=timezones.index(default_timezone))

    # Alinha o botão com o texto
    if st.sidebar.button("Sair da Conta", key="logout_btn"):
        # Remover ou setar como falso o cookie de logged_in
        controller.set('logged_in', False)  # Remover o estado de login
        controller.set('cliente_id', False)  # Opcional: limpar o cliente_id
        with st.spinner('Finalizando sessão...'):
            time.sleep(1)
            st.switch_page("paginas_app/login.py")  # Redireciona para a página de login

    if cliente_id == administrador:
        with st.sidebar.expander("Painel Administrador", expanded=True):
            if st.button("Acessar Painel Administrador"):
                st.switch_page("paginas_app/admin_page.py")  # Redireciona para a página de login

    with bottom():
        with st.expander("Clique para expandir a busca", expanded=True):
            my_grid = grid([2, 2, 2, 1], vertical_align="bottom")

            with st.spinner("Carregando países..."):
                countries = fetch_countries()

            # Buscar países
            if countries:
                country_names = [country['name'] for country in countries]

                # Selecionar o país armazenado, se disponível
                selected_country = my_grid.selectbox("Selecione o país:", country_names, index=country_names.index(
                    controller.get('selected_country')) if controller.get
                    ('selected_country') in country_names else 23)
                controller.set('selected_country', selected_country)
            else:
                erro = True
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

                                        # Filtra apenas os bookmakers selecionados
                                        filtered_bookmakers = [bookmaker for bookmaker in
                                                               odds_data["response"][0]["bookmakers"] if
                                                               bookmaker["name"] in selected_bookmakers]

                                        # Itera sobre os bookmakers já filtrados
                                        for bookmaker in filtered_bookmakers:
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
                                        print(f'Finalizei a data, segue: {data}')

                                        # Mostrar DataFrame no Streamlit
                                        if not df_bets.empty:
                                            # Adiciona um botão para calcular as previsões
                                            if saldo >= preco_inicial:
                                                if selected_game_info is not None:
                                                    if my_grid.button(f"${preco_inicial:.2f}  ►", disabled=erro,
                                                                      use_container_width=True):
                                                        (home_team_logo_url,
                                                         away_team_logo_url,
                                                         home_team_name,
                                                         away_team_name,
                                                         home_team_last_5_games,
                                                         away_team_last_5_games,
                                                         predictions,
                                                         team_id_home,
                                                         team_id_away) = get_prediction(fixture_id, preco_inicial,
                                                                                        cliente_id, 1)
                                                else:
                                                    st.write('Jogo sem informações para o robô.')
                                                    erro = True
                                            else:
                                                if my_grid.button('Recarregar', disabled=erro,
                                                                  use_container_width=True):
                                                    st.write("Recarga feita.")
                                        else:
                                            erro = True
                                            df_bets = None
                                            st.warning("Nenhuma odd encontrada para as casas e bets selecionadas. "
                                                       "Escolha outra opção de jogo ou de casa de apostas.")

                            else:
                                erro = True
                                # st.write("Nenhum jogo encontrado para a data e liga selecionadas.")
                                # pass
                        else:
                            # pass
                            erro = True
                            st.write("ID da liga não encontrado.")
                    else:
                        erro = True
                        st.write("Nenhuma liga encontrada para o país selecionado.")
            else:
                erro = True
                st.write("Nenhuma liga encontrada para o país selecionado.")





    if predictions is not None and df_bets is not None:
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
        stats_casa = stats_to_dataframe(st, home_team_stats, "Time da Casa")
        stats_fora = stats_to_dataframe(st, away_team_stats, "Time Visitante")

        st.write("**Inteligência Artificial Calculando:**")

        with st.spinner("Calculando previsão..."):
            llm = get_llm(selected_llm, 0)
            prompt = get_prompt(st,
                                selected_language,
                                user_name,
                                home_team_name,
                                away_team_name,
                                predictions,
                                home_team_last_5_results,
                                away_team_last_5_results,
                                stats_casa,
                                stats_fora,
                                bet_temperature,
                                df_bets,
                                llm,
                                selected_bets_favoritas
                                )
            st.write(prompt)

        # st.write(df_bets)
    else:
        st.write("Escolha um jogo e deixe a IA calcular a previsão.")
        st.sidebar.image('logo_atualizada.png', use_column_width=True)

elif cliente_id is False:
    all_cookies = controller.getAll()
    print(all_cookies)
    st.switch_page("paginas_app/login.py")