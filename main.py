import streamlit as st

# Definição das páginas
home = st.Page("paginas_app/redirect.py", title="Home")
login = st.Page("paginas_app/login.py", title="Login")
app = st.Page("paginas_app/app.py", title="App")
admin_page = st.Page("paginas_app/admin_page.py", title="Admin Page")
criar_conta = st.Page("paginas_app/criar_conta.py", title="Criar Conta")

# Navegação
pg = st.navigation([home, login, app, admin_page, criar_conta], position="hidden")
pg.run()
