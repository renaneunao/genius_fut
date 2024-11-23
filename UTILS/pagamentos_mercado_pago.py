import os
from dotenv import load_dotenv
import mercadopago
from datetime import datetime, timedelta
import requests

# Carrega as variáveis do arquivo .env
load_dotenv()
ACCESS_TOKEN = os.getenv("MERCADO_PAGO_ACCESS_TOKEN")


def criar_preferencia_pagamento(client_id, useremail, username, cpf, pais, quantidade, valor_em_dolar):
    if not all([client_id, useremail, username, cpf, pais]):
        return "Erro: Todos os campos obrigatórios devem ser preenchidos."

    sdk = mercadopago.SDK(ACCESS_TOKEN)

    data_atual = datetime.now()
    data_expiracao_fim = (data_atual + timedelta(days=1)).replace(hour=23, minute=59, second=59).strftime("%Y-%m-%dT%H:%M:%S.000-04:00")

    payment_data = {
        "auto_return": "all",
        "back_urls": {
            "success": "https://geniusfut.streamlit.app/atualizar_creditos",
            "failure": "https://geniusfut.streamlit.app/atualizar_creditos",
            "pending": "https://geniusfut.streamlit.app/atualizar_creditos"
        },
        "statement_descriptor": "GeniusFut",
        "external_reference": client_id,
        "items": [
            {
                "id": "1",
                "title": "GeniusFut - Credits",
                "quantity": quantidade,
                "unit_price": valor_em_dolar,
                "currency_id": "BRL",
                "description": f"Créditos de uso da plataforma GeniusFut (Valor em dólares: {quantidade:.2f} USD)",
                "category_id": "IA",

            }
        ],
        "payer": {
            "email": useremail,
            "name": username,
            "identification": {
                "type": "CPF",
                "number": cpf
            },
            "address": {
                "country": pais
            }
        },
        "payment_methods": {
            "excluded_payment_types": [{"id": "ticket"}],
            "installments": 2
        },
        "notification_url": "https://www.your-site.com/webhook",
        "expires": True,
        "expiration_date_to": data_expiracao_fim
    }

    try:
        result = sdk.preference().create(payment_data)
        payment = result["response"]
        return payment.get("init_point", "Erro: init_point não encontrado.")
    except Exception as e:
        return f"Erro ao criar a preferência de pagamento: {str(e)}"


def verificar_pagamento(st, client_id):
    """
    Verifica os pagamentos realizados por um cliente no Mercado Pago.

    Args:
        client_id (str): ID do cliente que será usado como referência externa.

    Returns:
        dict: Dados dos pagamentos encontrados ou uma mensagem de erro.
    """
    url = "https://api.mercadopago.com/v1/payments/search"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    params = {
        "sort": "date_created",
        "criteria": "desc",
        "external_reference": client_id
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        pagamentos = response.json()
        # st.write(pagamentos)
        return pagamentos  # Retorna o JSON completo com os resultados

    except requests.exceptions.RequestException as e:
        return {"status": "Erro", "mensagem": f"Erro ao buscar pagamentos: {str(e)}"}


