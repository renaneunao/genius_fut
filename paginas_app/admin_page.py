import pandas as pd
from UTILS.connection import get_connection
import streamlit as st
from UTILS.utils import verificar_cookies
from streamlit_cookies_controller import CookieController, RemoveEmptyElementContainer

administrador = 3

# Inicializa o controlador de cookies
controller = CookieController(key='cookies')
RemoveEmptyElementContainer()

# Configuração da página
st.set_page_config(page_title="Painel do Administrador", page_icon="icone_mini.png")

cliente_id, logged_in = verificar_cookies(controller)

if cliente_id == administrador:

    conn = get_connection()

    cursor = conn.cursor()

    # Opções de menu
    menu = st.selectbox("Escolha uma opção:", ["Listar Clientes", "Listar Credenciais", "Listar Acessos"])

    if menu == "Listar Clientes":
        st.subheader("Clientes")

        # Listar clientes
        cursor.execute(
            "SELECT id, usuario, nome, telefone, data_nascimento, pais FROM clientes")
        clientes = cursor.fetchall()
        df_clientes = pd.DataFrame(clientes,
                                   columns=["ID", "Usuário", "Nome", "Telefone", "Data de Nascimento", "País"])

        # Exibir a lista de clientes
        st.dataframe(df_clientes)

        # Selecionar cliente para edição
        cliente_edit = st.selectbox("Selecione o ID do cliente para editar:", df_clientes["ID"])

        if cliente_edit:
            # Consultar informações do cliente selecionado
            cursor.execute("SELECT * FROM clientes WHERE id = %s", (cliente_edit,))
            cliente = cursor.fetchone()

            # Formulário para editar informações do cliente
            nome = st.text_input("Nome", value=cliente[2])
            telefone = st.text_input("Telefone", value=cliente[3])
            data_nascimento = st.date_input("Data de Nascimento", value=cliente[4], format="DD/MM/YYYY")
            pais = st.text_input("País", value=cliente[5])  # Corrigido índice para 'pais'

            if st.button("Salvar"):
                cursor.execute("""
                    UPDATE clientes 
                    SET nome = %s, telefone = %s, data_nascimento = %s, pais = %s,  
                    WHERE id = %s
                """, (nome, telefone, data_nascimento, pais, cliente_edit))
                conn.commit()
                st.success("Cliente atualizado com sucesso!")

    elif menu == "Listar Credenciais":
        st.subheader("Credenciais")

        # Listar credenciais
        cursor.execute("SELECT id, usuario FROM credenciais")
        credenciais = cursor.fetchall()
        df_credenciais = pd.DataFrame(credenciais, columns=["ID", "Usuário"])

        # Exibir a lista de credenciais
        st.dataframe(df_credenciais)

        # Selecionar credencial para edição
        credencial_id = st.selectbox("Selecione o ID da credencial para editar:", df_credenciais["ID"])

        if credencial_id:
            # Consultar informações da credencial selecionada
            cursor.execute("SELECT * FROM credenciais WHERE id = %s", (credencial_id,))
            credencial = cursor.fetchone()

            # Formulário para editar informações da credencial
            usuario = st.text_input("Usuário", value=credencial[1])
            senha = st.text_input("Senha", value=credencial[2], type="password")

            if st.button("Salvar"):
                cursor.execute("UPDATE credenciais SET usuario = %s, senha = %s WHERE id = %s",
                               (usuario, senha, credencial_id))
                conn.commit()
                st.success("Credencial atualizada com sucesso!")

    elif menu == "Listar Acessos":
        st.subheader("Acessos dos Clientes")
        # Listar todos os clientes com LEFT JOIN para incluir clientes sem acessos

        cursor.execute(
            """
            SELECT c.id AS cliente_id, c.nome, ac.data_limite, ac.bypass 
            FROM clientes c 
            LEFT JOIN acesso_cliente ac ON ac.cliente_id = c.id
            """
        )
        acessos = cursor.fetchall()
        df_acessos = pd.DataFrame(acessos, columns=["ID do Cliente", "Nome", "Data Limite", "Bypass"])

        # Exibir a lista de acessos
        st.dataframe(df_acessos)

        # Selecionar um cliente para editar acesso
        cliente_edit = st.selectbox("Selecione o ID do Cliente para editar acesso:",
                                    df_acessos["ID do Cliente"].unique())

        # Verificar se o cliente já possui um acesso
        cursor.execute("SELECT * FROM acesso_cliente WHERE cliente_id = %s", (cliente_edit,))

        acesso_existente = cursor.fetchone()
        if acesso_existente:

            # Campos para edição
            nova_data_limite_edit = st.date_input("Nova Data Limite:",
                                                  value=acesso_existente[1])  # Assuming date is the second column

            novo_bypass_edit = st.number_input("Novo Valor do Bypass:", value=acesso_existente[2], min_value=0,
                                               max_value=1)  # Assuming bypass is the third column

            if st.button('Confirmar edição'):
                # Atualiza os dados de acesso
                cursor.execute(
                    "UPDATE acesso_cliente SET data_limite = %s, bypass = %s WHERE cliente_id = %s",
                    (nova_data_limite_edit, novo_bypass_edit, cliente_edit)
                )
                conn.commit()
                st.success("Acesso editado com sucesso!")
        else:
            st.warning("Nenhum acesso encontrado para este cliente.")

        # Fechar o cursor e a conexão
        cursor.close()
        conn.close()
else:
    st.write("Você não é um administrador!")