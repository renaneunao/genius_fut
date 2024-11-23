from UTILS.connection import get_connection
from UTILS.pagamentos_mercado_pago import verificar_pagamento
import streamlit as st
from UTILS.utils import verificar_cookies
from streamlit_cookies_controller import CookieController, RemoveEmptyElementContainer


# Configuração da página
st.set_page_config(page_title="Callback de Pagamentos", page_icon="icone_mini.png")

# Configuração do controlador de cookies
controller = CookieController(key='cookies')
RemoveEmptyElementContainer()

# Função para inserir créditos na tabela
def inserir_creditos(cliente_id, datahora, valor_compra, id_pagamento_mercado_pago):
    conn = get_connection()
    cursor = conn.cursor()

    # Verificar se o pagamento já foi registrado
    cursor.execute('''
        SELECT COUNT(*) FROM compras_creditos WHERE id_pagamento_mercado_pago = %s
    ''', (id_pagamento_mercado_pago,))
    count = cursor.fetchone()[0]

    if count == 0:
        # Inserir o crédito se o pagamento não foi registrado
        cursor.execute('''
            INSERT INTO compras_creditos (cliente_id, datahora, valor_compra, id_pagamento_mercado_pago)
            VALUES (%s, %s, %s, %s)
        ''', (cliente_id, datahora, valor_compra, id_pagamento_mercado_pago))
        conn.commit()
        result_message = f"Crédito inserido com sucesso para o pagamento {id_pagamento_mercado_pago}de {valor_compra} USD!"
    else:
        result_message = f"Pagamento com ID {id_pagamento_mercado_pago} de {valor_compra} USD já foi registrado."

    cursor.close()
    conn.close()
    return result_message

# Verificar callback e atualizar saldo
st.title("Callback de Pagamento")

with st.spinner("Recalculando saldo..."):
    try:
        cliente_id, logged_in = verificar_cookies(controller)

        if cliente_id:
            pagamentos = verificar_pagamento(st, cliente_id)

            if pagamentos.get("results"):
                for pagamento in pagamentos["results"]:
                    if pagamento.get('status') == "approved":
                        items = pagamento.get('additional_info', {}).get('items', [])
                        if items:
                            for item in items:
                                unit_price = float(item.get('unit_price', 0))

                                if unit_price > 0:
                                    mensagem = inserir_creditos(
                                        cliente_id=cliente_id,
                                        datahora=pagamento.get('date_created'),
                                        valor_compra=unit_price,
                                        id_pagamento_mercado_pago=pagamento.get('id')
                                    )
                                    st.success(mensagem)
                                else:
                                    st.warning(f"Pagamento ID {pagamento.get('id')} tem valor inválido.")
                        else:
                            st.warning(f"Pagamento ID {pagamento.get('id')} não contém itens.")
                    else:
                        st.info(f"Pagamento ID {pagamento.get('id')} não aprovado (status: {pagamento.get('status')}).")
            else:
                st.info("Nenhum pagamento encontrado para este cliente.")

                # Botão para retornar ao app
                if st.sidebar.button("Retornar ao app", key="retornar_app_btn"):
                    st.switch_page("paginas_app/app.py")  # Redireciona para a página de login

        elif cliente_id is False:
            all_cookies = controller.getAll()
            print(all_cookies)
            st.switch_page("paginas_app/login.py")

    except Exception as e:
        st.error(f"Erro ao processar callback: {e}")
