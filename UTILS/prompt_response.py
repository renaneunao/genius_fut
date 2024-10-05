from langchain_core.prompts import PipelinePromptTemplate, PromptTemplate

# Template principal para combinar tudo
full_template = """{orientacoes}

{dicas_apostas}

{estatisticas}

{temperatura}

{tabela_apostas}

{resultado_final}
"""

# 1. Orientações para resposta
orientacoes_template = """
### 1. Orientações para Resposta:

- **Linguagem**: Responda sempre no idioma selecionado: `{selected_language}`.
- **Personalização**: Dirija-se a mim pelo meu nome: `{user_name}`.
- **Especialização**: Você é um especialista em apostas online.
- **Confiança**: Responda com confiança e profissionalismo.
- **Cálculo de Aposta**: As apostas devem ser baseadas nas estatísticas e na temperatura fornecida.
"""

# 2. Dicas de Apostas
dicas_apostas_template = """
## 2. Dicas de Apostas:
- Nunca ofereça odds de 1.0.
- Não ofereça bets contraditórias, como vitória de um time e gols para o outro.
- O time da casa é: `{home_team_name}`.
- O time visitante é: `{away_team_name}`.
- Apostas mais ousadas para temperaturas quentes, mais seguras para frias.
- Uma api de Predictions disse isso, mas você não é obrigado a concordar. Apenas use de referência: `{predictions}`
"""

# 3. Estatísticas
estatisticas_template = """
## 3. Estatísticas:
- Últimos 5 jogos do time da casa: `{home_team_last_5_results}`.
- Últimos 5 jogos do time visitante: `{away_team_last_5_results}`.
- Desempenho geral do time da casa: `{stats_casa}`.
- Desempenho geral do time visitante: `{stats_fora}`.
"""

# 4. Temperatura da Aposta
temperatura_template = """
## 4. Temperatura da Aposta:
- Temperatura: `{bet_temperature}` (0 = aposta simples e segura, 1 = aposta ousada).
"""

# 5. Tabela de Apostas
tabela_apostas_template = """
## 5. Apostas Sugeridas:

Com base na temperatura de `{bet_temperature}`, as seguintes apostas foram escolhidas:

| Time Envolvido | Tipo de Aposta | Odds | Casa de Apostas |
|------------------|------------------------|--------|----------|
{df_bets}
"""

# 6. Resultado Final
resultado_final_template = """
## 6. Resultado Final:
- Apostas escolhidas com base na análise das estatísticas e na temperatura de apostas.
- Temperatura `{bet_temperature}` influenciou as apostas para serem {nivel_ousadia}.
- Odd final combinada para múltiplas: multiplique as odds para formar uma odd multipla resultante.
"""

# Montagem do Pipeline
input_prompts = [
    ("orientacoes", PromptTemplate.from_template(orientacoes_template)),
    ("dicas_apostas", PromptTemplate.from_template(dicas_apostas_template)),
    ("estatisticas", PromptTemplate.from_template(estatisticas_template)),
    ("temperatura", PromptTemplate.from_template(temperatura_template)),
    ("tabela_apostas", PromptTemplate.from_template(tabela_apostas_template)),
    ("resultado_final", PromptTemplate.from_template(resultado_final_template)),
]

# Criar o PromptTemplate principal
final_prompt_template = PromptTemplate.from_template(full_template)

# Agora, usamos o final_prompt_template no PipelinePromptTemplate
pipeline_prompt = PipelinePromptTemplate(
    final_prompt=final_prompt_template, pipeline_prompts=input_prompts
)

# Função para gerar o prompt final
def get_prompt(st, selected_language, user_name, home_team_name, away_team_name, predictions, home_team_last_5_results,
               away_team_last_5_results, stats_casa, stats_fora, bet_temperature, df_bets):
    bet_temperature = float(bet_temperature)
    nivel_ousadia = "seguras e simples" if bet_temperature <= 0.3 else "medianas com algumas combinações" if bet_temperature <= 0.6 else "ousadas e com múltiplas"

    # Dados para preencher o pipeline
    prompt_data = {
        "selected_language": selected_language,
        "user_name": user_name,
        "home_team_name": home_team_name,
        "away_team_name": away_team_name,
        "predictions": predictions,
        "home_team_last_5_results": home_team_last_5_results,
        "away_team_last_5_results": away_team_last_5_results,
        "stats_casa": stats_casa,
        "stats_fora": stats_fora,
        "bet_temperature": bet_temperature,
        "df_bets": df_bets,
        "nivel_ousadia": nivel_ousadia
    }

    # Gera o prompt final usando o pipeline
    st.write(df_bets)
    return pipeline_prompt.format(**prompt_data)
