import pandas as pd
from UTILS.connection import get_connection
import streamlit as st
from UTILS.utils import verificar_cookies
from streamlit_cookies_controller import CookieController, RemoveEmptyElementContainer

administrador = 3

# Configuração da página
st.set_page_config(page_title="Painel do Administrador", page_icon="icone_mini.png")

# Inicializa o controlador de cookies
controller = CookieController(key='cookies')
RemoveEmptyElementContainer()

cliente_id, logged_in = verificar_cookies(controller)

if cliente_id == administrador:

    conn = get_connection()

    cursor = conn.cursor()

    # Opções de menu
    menu = st.selectbox("Escolha uma opção:", ["Listar Clientes", "Listar Credenciais", "Listar Acessos", "Listar e Editar Saldo"])

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
        # Query para listar todos os clientes com LEFT JOIN para incluir clientes sem acessos
        cursor.execute(
            """
        SELECT c.id AS cliente_id, IFNULL(ac.bypass, 0) AS bypass, IFNULL(ac.trial_credits, 0) AS trial_credits
        FROM clientes c 
        LEFT JOIN acesso_cliente ac ON ac.cliente_id = c.id
        """
        )
        acessos = cursor.fetchall()
        # Criando DataFrame para exibir os acessos
        df_acessos = pd.DataFrame(acessos, columns=["ID do Cliente", "Bypass", "Trial Credits"])
        # Exibir a lista de acessos
        st.dataframe(df_acessos)
        # Selecionar um cliente para editar acesso
        cliente_edit = st.selectbox("Selecione o ID do Cliente para editar acesso:",
                                    df_acessos["ID do Cliente"].unique())
        if cliente_edit:
            # Verificar se o cliente já possui um acesso
            cursor.execute("SELECT * FROM acesso_cliente WHERE cliente_id = %s", (cliente_edit,))
            acesso_existente = cursor.fetchone()
            if acesso_existente:
                novo_bypass_edit = st.number_input("Novo Valor do Bypass:", value=acesso_existente[2], min_value=0,
                                                   max_value=1)
                novo_trial_credits_edit = st.number_input("Novo Valor de Trial Credits:", value=1,
                                                          min_value=0)
                if st.button('Confirmar edição'):
                    # Atualiza os dados de acesso
                    cursor.execute(
                        "UPDATE acesso_cliente SET bypass = %s, trial_credits = %s WHERE cliente_id = %s",
                        (novo_bypass_edit, novo_trial_credits_edit, cliente_edit)
                    )
                    conn.commit()
                    st.success("Acesso editado com sucesso!")
            else:
                st.warning("Nenhum acesso encontrado para este cliente.")
        # Fechar o cursor e a conexão
        cursor.close()
        conn.close()

    elif menu == "Listar e Editar Saldo":
        st.subheader("Saldo dos Clientes")

        # Listar saldo dos clientes
        cursor.execute('''
            SELECT c.id, c.nome
            FROM clientes c
        ''')
        clientes = cursor.fetchall()

        # Criar DataFrame para armazenar saldos
        saldo_data = []
        for cliente in clientes:
            cliente_id = cliente[0]

            # Obter o total de compras (créditos) do cliente
            cursor.execute('''
                SELECT IFNULL(SUM(COALESCE(cp.valor_compra, 0)), 0) AS total_creditos
                FROM compras_creditos cp
                WHERE cp.cliente_id = %s
            ''', (cliente_id,))
            total_creditos = cursor.fetchone()[0]

            # Obter o total de consumos do cliente
            cursor.execute('''
                SELECT IFNULL(SUM(COALESCE(cs.valor_consumo, 0)), 0) AS total_consumos
                FROM consumos cs
                WHERE cs.cliente_id = %s
            ''', (cliente_id,))
            total_consumos = cursor.fetchone()[0]

            # Calcular o saldo
            saldo = total_creditos - total_consumos
            saldo_data.append([cliente_id, cliente[1], saldo])

        # Exibir a tabela de saldos
        df_saldos = pd.DataFrame(saldo_data, columns=["ID do Cliente", "Nome", "Saldo"])
        st.dataframe(df_saldos)

        # Selecionar cliente para editar saldo
        cliente_edit = st.selectbox("Selecione o ID do cliente para editar saldo:", df_saldos["ID do Cliente"])
        if cliente_edit:

            # Obter o total de compras (créditos) do cliente
            cursor.execute('''
                SELECT IFNULL(SUM(COALESCE(cp.valor_compra, 0)), 0) AS total_creditos
                FROM compras_creditos cp
                WHERE cp.cliente_id = %s
            ''', (cliente_edit,))
            total_creditos = cursor.fetchone()[0]

            # Obter o total de consumos do cliente
            cursor.execute('''
                SELECT IFNULL(SUM(COALESCE(cs.valor_consumo, 0)), 0) AS total_consumos
                FROM consumos cs
                WHERE cs.cliente_id = %s
            ''', (cliente_edit,))
            total_consumos = cursor.fetchone()[0]

            # Calcular o saldo
            saldo_cliente = total_creditos - total_consumos
            st.write(f"O saldo atual do cliente {cliente_edit} é: {saldo_cliente:.2f}")

            # Adicionar/Remover saldo via compras ou consumos
            st.subheader("Adicionar/Remover Saldo")

            # Seleciona a opção para adicionar ou remover saldo
            acao = st.selectbox("Escolha uma ação:", ["Adicionar Saldo", "Remover Saldo"])
            valor = st.number_input(f"Valor para {acao}:", min_value=0.0, format="%.2f")
            if st.button(f"{acao} Saldo"):
                if acao == "Adicionar Saldo":
                    # Adiciona um valor na tabela de compras de créditos
                    cursor.execute(
                        "INSERT INTO compras_creditos (cliente_id, datahora, valor_compra) VALUES (%s, NOW(), %s)",
                        (cliente_edit, valor)
                    )
                    conn.commit()
                    st.success(f"Saldo de {valor} adicionado ao cliente {cliente_edit}.")

                elif acao == "Remover Saldo":
                    # Adiciona um valor na tabela de consumos (removendo saldo)
                    cursor.execute(
                        "INSERT INTO consumos (cliente_id, datahora, valor_consumo, configuracao_consumo) VALUES (%s, NOW(), %s, 'Remoção de saldo')",
                        (cliente_edit, valor)
                    )
                    conn.commit()
                    st.success(f"Saldo de {valor} removido do cliente {cliente_edit}.")
        # Fechar o cursor e a conexão
        cursor.close()
        conn.close()



else:
    st.write("Você não é um administrador!")