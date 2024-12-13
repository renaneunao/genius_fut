import os
import openai
from dotenv import load_dotenv
from langchain.chains import LLMChain
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers.json import JsonOutputParser

parser = JsonOutputParser()

def get_prompt(st, selected_language, user_name, home_team_name, away_team_name, predictions, home_team_last_5_results,
               away_team_last_5_results, stats_casa, stats_fora, bet_temperature, df_bets, llm, bets_usuario):
    print(f'AQUI ESTÃO AS BETS PREFERIDAS DO USUARIO: ========================='
          f'{bets_usuario}')
    # Substituir 'Home' e 'Away' pelo nome do time correspondente
    df_bets['Valor'] = df_bets['Valor'].apply(
        lambda x: home_team_name if x == 'Home' else away_team_name if x == 'Away' else x)

    # Carregar a chave da API do OpenAI do .env
    load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")

    # Função que monta a linha de tendência
    def futebol_trend_chain(home_team_name, away_team_name, predictions, home_team_last_5_results,
                            away_team_last_5_results, stats_casa, stats_fora):
        prompt_template = """
        Você é um especialista em futebol e vai criar uma linha de tendência para a previsão do resultado do jogo entre 
        {home_team_name} e {away_team_name}. 
        Abaixo estão as estatísticas e resultados recentes para ambos os times:

        - Nome do time da casa: {home_team_name}
        - Nome do time de fora: {away_team_name}
        - Resultados dos últimos 5 jogos do time da casa: {home_team_last_5_results}
        - Resultados dos últimos 5 jogos do time de fora: {away_team_last_5_results}
        - Estatísticas da casa: {stats_casa}
        - Estatísticas de fora: {stats_fora}

        As previsões fornecidas são as seguintes:
        {predictions}

        Com base nisso, crie uma linha de tendência que contenha os seguintes campos:
        - time_favoravel: o time mais provável de vencer.
        - peso_favoritismo: um valor entre 0 e 1 indicando a força da previsão.
        - quantidade_gols_prevista_casa: previsão de gols para o time da casa.
        - quantidade_gols_prevista_fora: previsão de gols para o time de fora.
        - quantidade_cantos_prevista_casa: previsão de escanteios para o time da casa.
        - quantidade_cantos_prevista_fora: previsão de escanteios para o time de fora.
        - quantidade_cartoes_prevista_casa: previsão de cartões para o time da casa.
        - quantidade_cartoes_prevista_fora: previsão de cartões para o time de fora.
        - quantidade_finalizacoes_prevista_casa: previsão de finalizações para o time da casa.
        - quantidade_finalizacoes_prevista_fora: previsão de finalizações para o time de fora.

        **Retorne apenas o resultado como um dicionário JSON, sem formatação adicional.**
        """

        prompt = PromptTemplate(
            input_variables=["home_team_name", "away_team_name", "home_team_last_5_results", "away_team_last_5_results",
                             "stats_casa", "stats_fora", "predictions"],
            template=prompt_template,
            partial_variables={"format_instructions": parser.get_format_instructions()}
        )

        chain = prompt | llm | parser
        trend_result = chain.invoke({
            "home_team_name": home_team_name,
            "away_team_name": away_team_name,
            "home_team_last_5_results": home_team_last_5_results,
            "away_team_last_5_results": away_team_last_5_results,
            "stats_casa": stats_casa,
            "stats_fora": stats_fora,
            "predictions": predictions
        })

        return trend_result

    # Função que avalia as bets com base na linha de tendência e encontra as 20 melhores
    def bet_expert_chain(trend_line, df_bets, selected_bets):
        bet_prompt_template = """
        Você é um especialista em apostas de futebol. Aqui está a linha de tendência prevista para o jogo:

        Linha de tendência:
        {trend_line}

        Abaixo está uma lista de apostas disponíveis para o jogo:

        Apostas:
        {df_bets}

        Sua tarefa é analisar as apostas e retornar as 20 melhores opções, com base na linha de tendência fornecida. 
        Diversifique em uma divisão perfeita entre diferentes tipos de apostas, preferidas do usuário:  
        {selected_bets}
        
        Para cada aposta, retorne as seguintes informações:

        - Casa: a casa de aposta ou time associado
        - Bet: o nome da aposta, ex: Casa Over 9.5 cantos
        - Sujeito: casa, fora ou ambos (especifique o nome do time, ou escreva ambos para apostas que incluam os dois times)
        - ODD: a odd associada à aposta
        
        ** Nunca liste entre as melhores opções bets contra o time favorito **

        Retorne o resultado em formato JSON com uma lista de dicionários contendo essas quatro informações.
        """

        bet_prompt = PromptTemplate(input_variables=["trend_line", "df_bets", "selected_bets"],
                                    template=bet_prompt_template,
                                    partial_variables={"format_instructions": parser.get_format_instructions()})
        bet_chain = bet_prompt | llm | parser

        best_bets_result = bet_chain.invoke({
            "trend_line": trend_line,
            "df_bets": df_bets.to_dict(orient='records'),  # Converter o DataFrame para dicionário
            "selected_bets": selected_bets
        })

        return best_bets_result

    with st.spinner('Calculando a linha de tendência do jogo 📈 ...'):
        # Gerar linha de tendência usando futebol_trend_chain
        trend_line = futebol_trend_chain(home_team_name, away_team_name, predictions, home_team_last_5_results,
                                         away_team_last_5_results, stats_casa, stats_fora)

    with st.spinner('Escolhendo as melhores apostas para o jogo 🎯 ...'):
        # Encontrar as 20 melhores bets usando bet_expert_chain
        top_bets = bet_expert_chain(trend_line, df_bets, bets_usuario)

    def simple_bet_expert_chain(top_bets, trend_line, selected_bets):

        simple_bet_prompt_template = """
        Você é um especialista em apostas de futebol. Sua tarefa é analisar as apostas fornecidas e a linha de tendência 
        para selecionar as melhores opções para apostas simples, considerando escolher no mínimo uma opção de cada
        uma das preferências do usuário:
        {selected_bets}

        Linha de tendência:
        {trend_line}

        Apostas disponíveis:
        {top_bets}

        Por favor, retorne as melhores opções de apostas simples, levando em consideração as informações 
        fornecidas e a linha de tendência. Para cada aposta, retorne as seguintes informações:

        - Casa: a casa de aposta ou time associado
        - Aposta: o tipo de aposta
        - Info Aposta: o quantitativo a ser apostado
        - Sujeito: casa, fora ou ambos
        - ODD: a odd associada à aposta (o valor multiplicador)

        Retorne o resultado em formato JSON com uma lista de dicionários contendo essas cinco informações.
        """

        simple_bet_prompt = PromptTemplate(input_variables=["selected_bets", "top_bets", "trend_line"],
                                           template=simple_bet_prompt_template,
                                           partial_variables={"format_instructions": parser.get_format_instructions()})
        simple_bet_chain = simple_bet_prompt | llm | parser

        simple_bet_chain_result = simple_bet_chain.invoke({
            "selected_bets": selected_bets,
            "top_bets": top_bets,
            "trend_line": trend_line,
        })

        return simple_bet_chain_result

    def multiple_bet_expert_chain(top_bets, trend_line, selected_bets):

        multiple_bet_prompt_template = """
        Você é um especialista em apostas de futebol. Sua tarefa é analisar as apostas fornecidas e a linha de tendência 
        para montar as melhores opções de apostas múltiplas, considerando mesclar entre pelo menos uma de cada uma
        das opções preferidas do usuário:
        {selected_bets} 

        Linha de tendência:
        {trend_line}

        Apostas disponíveis:
        {top_bets}

        Instruções para Definição de Múltiplas:

        1. **Múltiplas**: Múltiplas são apostas que devem ocorrer em conjunto para serem bem-sucedidas. 
        O objetivo é escolher combinações de apostas que têm alta probabilidade de acontecerem juntas, 
        como a vitória de um time e a previsão de um número mínimo de gols. 

        2. **Apostas Impossíveis**: Evite combinações que não podem ocorrer simultaneamente, como vitória e empate para 
        o mesmo time. Essas combinações são inviáveis e não devem ser incluídas.

        3. **Apostas Contraditórias ou Redundantes**: Não crie apostas que se contradizem ou são redundantes. 
        Por exemplo, evite "Mais de 1.5 gols" e "Menos de 3.5 gols", pois isso só permite o resultado de 2 gols. 
        Prefira apostas diretas, como "Exatos 2 gols", ou combinações mais viáveis, baseadas nas condições do jogo.

        4. **Condições para Múltiplas**: Se incluir apostas como "Ambas Marcam" e "Time A Vence", a aposta 
        "Over 2.5 gols" obrigatoriamente precisa acontecer, então a casa não pagaria a mais por isso. 
        Nesse caso, "Over 2.5 gols" é nula e não deve ser incluída na múltipla.
        
        5. ** Não ofereça apostas múltiplas em casas de apostas diferentes. As múltiplas devem ser feitas exclusivamente 
        em uma única plataforma. Por exemplo, se você tiver três apostas na casa A, elas formarão uma única múltipla. 
        Da mesma forma, três apostas na casa B formarão outra múltipla. Nunca misture apostas da casa A com apostas da 
        casa B na mesma múltipla. **
        
        6. ** Múltiplas não são várias apostas avulsas, mas a combinação de várias apostas que precisam acontecer
         em conjunto, para que o resultado seja positivo, por exemplo: "bet: Casa vence + bet: Mais de 9 cantos no jogo.**

        Por favor, monte as melhores apostas múltiplas com base nas informações fornecidas. 
        Para cada múltipla, retorne as seguintes informações:

        - Casa: a casa de aposta ou time associado
        - Aposta: o tipo de aposta (no mínimo duas apostas, cada uma em uma chave)
        - Info Aposta: quantitativo da aposta (ex: 1:0)
        - Sujeito: casa, fora ou ambos
        - ODD: a odd de cada uma das bets (valor do multiplicador)
        - ODD FINAL: uma chave retornando o valor final da multiplicação dos multiplicadores de ODD. Não confunda com a 
        info da aposta.

        Retorne o resultado em formato JSON com uma lista de dicionários contendo essas informações.
        """

        multiple_bet_prompt = PromptTemplate(input_variables=["selected_bets", "top_bets", "trend_line"],
                                             template=multiple_bet_prompt_template,
                                             partial_variables={"format_instructions": parser.get_format_instructions()})
        multiple_bet_chain = multiple_bet_prompt | llm | parser

        multiple_bet_chain_result = multiple_bet_chain.invoke({
            "selected_bets": selected_bets,
            "top_bets": top_bets,
            "trend_line": trend_line,
        })

        return multiple_bet_chain_result

    with st.spinner('Calculando apostas simples 💸 ...'):
        simple_bet = simple_bet_expert_chain(top_bets, trend_line, bets_usuario)
    with st.spinner('Agora calculando as múltiplas 🤑 ...'):
        multiple_bet = multiple_bet_expert_chain(top_bets, trend_line, bets_usuario)

    def betting_expert_report(st, selected_language, user_name, simple_bet, multiple_bet, stats_casa, stats_fora,
                              home_team_name, away_team_name, home_team_last_5_results, away_team_last_5_results):

        if user_name is None:
            user_name = ''
        prompt_show_info = """
            Você é um especialista em apostas de futebol. Sua tarefa é analisar as apostas simples e múltiplas fornecidas 
            e apresentar um relatório claro e detalhado para o usuário final montando uma tabela para as bets simples
            e outra tabela para as bets múltiplas.
            
            - O time da casa é: `{home_team_name}`.
            - O time visitante é: `{away_team_name}`.
            
            ### 1. Orientações para Resposta:
            - **Linguagem**: Responda sempre no idioma selecionado: `{selected_language}`.
            - **Personalização**: Dirija-se a mim pelo meu nome: `{user_name}`.
            - **Especialização**: Você é um especialista em apostas online.
            - **Confiança**: Responda com confiança e profissionalismo.
            
            ## 2. Estatísticas:
            - Últimos 5 jogos do time da casa: `{home_team_last_5_results}`.
            - Últimos 5 jogos do time visitante: `{away_team_last_5_results}`.
            - Desempenho geral do time da casa: `{stats_casa}`.
            - Desempenho geral do time visitante: `{stats_fora}`.
    
            1. **Apostas Simples**: Voce recebeu um JSON contendo apostas simples, incluindo informações como casa de aposta, 
            tipo de aposta, sujeito e odd. Explique cada aposta de forma concisa e clara.
            Json Simple Bet:
            {simple_bet}
            
            2. **Apostas Múltiplas**: Receba um JSON contendo apostas múltiplas, que são combinações de apostas que têm 
            alta probabilidade de ocorrerem juntas. Para cada múltipla, forneça detalhes como casa de aposta, 
            tipo de aposta, sujeito e a odd final, que é o resultado da multiplicação das odds incluídas.
            Json Multiple Bet:
            {multiple_bet}
            
            3. **Análise**: Inclua uma análise final que destaque a viabilidade das apostas, mencionando as estatísticas recebidas. 
            O objetivo é garantir que as apostas apresentadas tenham alta probabilidade de sucesso.
            
            Apresente o relatório de forma estruturada e amigável, assegurando que o usuário final compreenda facilmente 
            as informações e a lógica por trás das apostas recomendadas, e se ficar visualmente legal, adicione emojis de fogo,
            ou relacionados à dinheiro, foguete, etc.
        """

        bet_show_prompt = PromptTemplate(input_variables=["home_team_name", "away_team_name", "selected_language",
                                                              "user_name", "home_team_last_5_results",
                                                              "away_team_last_5_results", "stats_casa",
                                                              "stats_fora", "simple_bet", "multiple_bet", "user_name"],
                                             template=prompt_show_info)
        bet_show_chain = LLMChain(prompt=bet_show_prompt, llm=llm)

        with st.spinner('Finalizando ideias...'):
            bet_show_result = bet_show_chain.run({
                "home_team_name": home_team_name,
                "away_team_name": away_team_name,
                "selected_language": selected_language,
                "user_name": user_name,
                "home_team_last_5_results": home_team_last_5_results,
                "away_team_last_5_results": away_team_last_5_results,
                "stats_casa": stats_casa,
                "stats_fora": stats_fora,
                "simple_bet": simple_bet,
                "multiple_bet": multiple_bet,
            })

        return bet_show_result

    return betting_expert_report(st, selected_language, user_name, simple_bet, multiple_bet, stats_casa, stats_fora,
                                 home_team_name, away_team_name, home_team_last_5_results, away_team_last_5_results)

