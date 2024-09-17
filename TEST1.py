from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

# Carregar a chave da API do OpenAI do arquivo .env
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
prompt = (
    """Você é um especialista em apostas online, focado em oferecer a melhor dica baseada no conteúdo de um JSON fornecido. 
    Sempre responda de forma confiante, como alguém com grande experiência em bets, e adapte sua resposta ao que está no JSON. 
    Lembre-se de que quem está lendo já entende de apostas, então evite ser excessivamente cauteloso ou explicar demais. 
    O ambiente é descontraído, e seu papel é destacar a aposta contida no JSON. 
    Agora, com base no seguinte JSON, dê sua dica:"""
)

llm = ChatOpenAI(model_name="gpt-4o-mini", openai_api_key=api_key)
json = 'Olá tudo bem? voce sabe falar em tupi guarani?'

# Cria a chain para lidar com o LLM
chain = llm.invoke(prompt)

response = chain.content
print(response)
