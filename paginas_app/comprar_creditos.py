from UTILS.connection import get_connection
import streamlit as st
from streamlit_cookies_controller import CookieController, RemoveEmptyElementContainer
from UTILS.pagamentos_mercado_pago import criar_preferencia_pagamento, verificar_pagamento
from UTILS.utils import verificar_cookies, obter_cotacao_dolar
from UTILS.connection import get_connection


# Configuração da página
st.set_page_config(page_title="Comprar Créditos", page_icon="icone_mini.png")

# Configuração do controlador de cookies
controller = CookieController(key='cookies')
RemoveEmptyElementContainer()

# Função para inserir créditos na tabela
def inserir_creditos(cliente_id, datahora, valor_compra, id_pagamento_mercado_pago):
    conn = get_connection()
    cursor = conn.cursor()

    # Verificar se o pagamento já foi registrado com o mesmo id_pagamento_mercado_pago
    cursor.execute('''
        SELECT COUNT(*) FROM compras_creditos WHERE id_pagamento_mercado_pago = %s
    ''', (id_pagamento_mercado_pago,))
    count = cursor.fetchone()[0]

    # Se não houver duplicação, inserir o crédito
    if count == 0:
        cursor.execute('''
            INSERT INTO compras_creditos (cliente_id, datahora, valor_compra, id_pagamento_mercado_pago)
            VALUES (%s, %s, %s, %s)
        ''', (cliente_id, datahora, valor_compra, id_pagamento_mercado_pago))

        # Commit para salvar as mudanças
        conn.commit()
        st.success("Crédito inserido com sucesso!")
    else:
        st.warning(f"Pagamento com ID {id_pagamento_mercado_pago} já foi registrado.")

    cursor.close()
    conn.close()

# Verificar cookies e autenticação
cliente_id, logged_in = verificar_cookies(controller)

# Redirecionar para a tela de login se não houver `cliente_id`
if cliente_id:
    cotacao_dolar = obter_cotacao_dolar(st)
    if cotacao_dolar:
        st.info(f"Cotação atual do dólar: R$ {cotacao_dolar:.2f}")
        # Input para o valor a ser comprado (em dólares)
        valor = st.number_input("Digite o valor em dólares que deseja comprar:", min_value=5.0, format="%.2f")

        # Botão para criar a ordem
        if st.button("Criar Ordem de Compra"):
            if valor > 0:
                # Dados do cliente (poderiam ser capturados de um banco ou sessão)
                useremail = "usuario@exemplo.com"  # Exemplo de e-mail do usuário
                username = "Nome do Usuário"  # Nome do usuário
                cpf = "12345678900"  # CPF do usuário
                pais = "BR"  # País do usuário (Brasil, por exemplo)
                valor_em_dolar = valor
                quantidade = cotacao_dolar
                st.write(f"Valor a pagar em reais: ${valor} * {cotacao_dolar}(cotação) = R${valor*cotacao_dolar:.2f}")


                # Criar preferência de pagamento
                link_pagamento = criar_preferencia_pagamento(client_id=cliente_id,
                                                             useremail=useremail,
                                                             username=username,
                                                             cpf=cpf,
                                                             pais=pais,
                                                             valor_em_dolar=valor_em_dolar,
                                                             quantidade=quantidade)

                if link_pagamento.startswith("http"):
                    # Exibir o link de pagamento em um iframe com rolagem
                    with st.spinner('Carregando página de compra...'):
                        st.components.v1.iframe(src=link_pagamento, width=800, height=600, scrolling=True)
                else:
                    st.error(f"Erro ao criar o link de pagamento: {link_pagamento}")
            else:
                st.warning("Por favor, insira um valor válido para comprar créditos.")

        # Botão para listar compras
        if st.button("Recalcular Saldo"):
            st.subheader("Pagamentos Realizados")
            pagamentos = verificar_pagamento(st, cliente_id)

            if pagamentos.get("results"):
                for pagamento in pagamentos["results"]:
                    # Verificar se o pagamento está com status "approved"
                    if pagamento.get('status') == "approved":
                            # Obtenha os itens dentro de "additional_info"
                            items = pagamento.get('additional_info', {}).get('items', [])

                            if items:
                                # Para cada item, pega o unit_price e calcula o valor total em dólar
                                for item in items:
                                    # Pega o valor unitário em dólar
                                    unit_price = float(item.get('unit_price', 0))  # Garante que é um número

                                    if unit_price > 0:
                                        # Exibe a quantidade, o valor pago e o valor total em dólares
                                        st.write(f"Valor unitário (em dólares): {unit_price:.2f} USD")

                                        # Exibe os detalhes do pagamento
                                        st.markdown(f"""
                                        - **ID do Pagamento**: {pagamento.get('id')}
                                        - **Status**: {pagamento.get('status')}
                                        - **Valor total pago (em BRL)**: {pagamento.get('transaction_amount')} {pagamento.get('currency_id')}
                                        - **Data de Criação**: {pagamento.get('date_created')}
                                        """)

                                        # Inserir na tabela de compras de créditos
                                        inserir_creditos(
                                            cliente_id=cliente_id,
                                            datahora=pagamento.get('date_created'),
                                            valor_compra=unit_price,
                                            id_pagamento_mercado_pago=pagamento.get('id')
                                        )
                                    else:
                                        st.warning(f"Pagamento ID {pagamento.get('id')} tem quantidade ou preço inválido.")
                            else:
                                # Se não houver itens, exibe uma mensagem de aviso
                                st.warning(f"Pagamento ID {pagamento.get('id')} não tem itens registrados.")
                    else:
                        st.info(
                            f"Pagamento ID {pagamento.get('id')} não está aprovado (status: {pagamento.get('status')}).")
            else:
                st.info("Nenhum pagamento encontrado para este cliente.")

        # Botão para retornar ao app
        if st.sidebar.button("Retornar ao app", key="retornar_app_btn"):
            st.switch_page("paginas_app/app.py")  # Redireciona para a página de login

elif cliente_id is False:
    all_cookies = controller.getAll()
    print(all_cookies)
    st.switch_page("paginas_app/login.py")
