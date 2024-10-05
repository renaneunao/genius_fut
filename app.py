from datetime import datetime
import pytz
import pandas as pd

from UTILS.admin_page import admin_page
from UTILS.utils import get_prediction, stats_to_dataframe
from UTILS.login import login
from UTILS.connection import get_connection
from UTILS.st_cache_functions import (fetch_timezones,
                                      fetch_countries,
                                      fetch_fixtures,
                                      fetch_leagues,
                                      fetch_team_stats,
                                      get_bookmakers,
                                      fetch_odds)
from UTILS.listas_bets import bets_gols, bets_cartoes, bets_escanteios
from UTILS.lista_languages import languages
from UTILS.prompt_response import get_prompt

from streamlit_extras.colored_header import colored_header
from streamlit_extras.bottom_container import bottom
from streamlit_extras.grid import grid


def main_page(st, controller, premium, administrador, llm):

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

    cliente_id = controller.get('cliente_id')
    if cliente_id:
        conn = get_connection()
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
            st.write("Cliente não encontrado.")
            st.sidebar.image('logo_atualizada.png', use_column_width=True)
            login(st, controller)
            st.rerun()

        conn.close()

        timezones = fetch_timezones()
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

        season = pd.to_datetime(date).year

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

        # Sidebar para configurações
        with st.sidebar.expander("Configurações Gerais"):
            st.title("Configurações Gerais")

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
            user_name = st.text_input("Digite seu nome:", value=user_name_cookie)
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

            controller.set('bet_temperature', bet_temperature)

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
            )

            # Expandir os grupos selecionados para incluir todas as bets
            selected_bets = []
            for group in selected_groups:
                selected_bets.extend(bet_groups[group])

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
            controller.set('cliente_id', False)  # Opcional: limpar o cliente_id
            # Redirecionar para a página de login
            st.success("Você saiu da conta.")
            login(st, controller)
            st.rerun()

        if user_name_cookie == administrador:
            with st.sidebar.expander("Painel Administrador", expanded=True):
                admin_page(st, controller)


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
                                    df_bets)
                # Cria a chain para lidar com o LLM
                chain = llm.invoke(prompt)

                response = chain.content

                st.write(response)
        else:
            st.write("Escolha um jogo e deixe a IA calcular a previsão.")
            st.sidebar.image('logo_atualizada.png', use_column_width=True)

    else:
        controller.set('logged_in', False)
        controller.set('cliente_id', False)
        login(st, controller)