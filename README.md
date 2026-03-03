# ⚽ Genius Fut 🏟️

O **Genius Fut** é uma aplicação baseada em `Streamlit` desenvolvida com um conceito de *freemium / pay-per-use*, onde usuários autênticos possuem "créditos" vinculados aos seus logins para processar ou acessar dados focados em análises inteligentes de Futebol. 

## 🏗 Estrutura da UI
A modelagem do projeto não retém tudo em um arquivo só. Para manter o código limpo, a infraestrutura das telas usa a característica de **Multi-Page App**:
- **`main.py`**: A espinha norte e ponto de entrada ocultando a sidebar nativa do Streamlit com rotas blindadas.
- **`/paginas_app/`**: Diretório segmentado contendo sub-apps como `login.py`, interfaces gerenciais (`admin_page.py`) e painéis de conversão transacionais (`comprar_creditos.py`, `atualizar_creditos.py`).
- **Recursos Visuais**: Conta com miniaturas e logomarcas em diretórios estáticos na raiz (`logo_genius_fut.jpg`).

## 🛠️ Tecnologias e Configuração
A stack envolve processamento rápido visual sem perder força do backend Python.
Possui pacotes locais declarados em `requirements.txt` com as especificidades nativas para conectar banco de dados (seja Postgres via `psycopg2` ou Firebase para autenticação), consumos matemáticos via `Pandas` e scripts sob a pasta `/UTILS/`.

## 🚀 Instalando & Executando

1. Recomendado o uso de um venv local.
2. Instale as dependências visuais e lógicas:
```bash
pip install -r requirements.txt
```
3. Inicialize a UI:
```bash
streamlit run main.py
```
O painel de login será o primeiro a renderizar na porta oficial redirecionando para views autorizadas!
