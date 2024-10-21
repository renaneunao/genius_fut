from UTILS.connection import get_connection

def criar_nova_conta(st, controller, dias_acesso):
    # Exibir informações do controller
    print(f'Logged_In Criar Nova Conta: {controller.get("logged_in")}')
    print(f'Cliente Criar Nova Conta: {controller.get("cliente_id")}')

    st.title("Criar Nova Conta")

    # Inputs do usuário
    usuario = st.text_input("Usuário", key='text_input_criar_usuario')
    senha = st.text_input("Senha", type='password', key='text_input_criar_senha')
    confirmar_senha = st.text_input("Confirmar Senha", type='password', key='text_input_criar_confirmar_senha')
    nome = st.text_input("Nome Completo", key='text_input_criar_nome_completo')
    telefone = st.text_input("Telefone", key='text_input_criar_telefone')
    data_nascimento = st.date_input("Data de Nascimento", format="DD/MM/YYYY", key='text_input_criar_data_nascimento')
    pais = st.text_input("País", key='text_input_criar_pais')

    col1, col2 = st.columns(2)
    with col1:
        # Validação ao clicar no botão "Criar Conta"
        if st.button("Criar Conta"):
            # Verificar se todos os campos estão preenchidos
            if not usuario or not senha or not confirmar_senha or not nome or not telefone or not data_nascimento or not pais:
                st.error("Todos os campos são obrigatórios!")
                return

            # Verificar se as senhas correspondem
            if senha != confirmar_senha:
                st.error("As senhas não correspondem!")
                return

            # Se as validações passarem, criar a conta
            criar_conta(st, controller, usuario, senha, nome, telefone, data_nascimento, pais, dias_acesso)

    with col2:
        # Botão para voltar à tela de login
        if st.button("Já tem uma conta? Faça login"):
            st.session_state['screen'] = 'login'  # Muda a tela para login
            st.rerun()


def criar_conta(st, controller, usuario, senha, nome, telefone, data_nascimento, pais, dias_acesso):
    # Exibir informações do controller
    print(f'Logged_In Criar Conta: {controller.get("logged_in")}')
    print(f'Cliente Criar Conta: {controller.get("cliente_id")}')

    # Conectar ao banco de dados
    conn = get_connection()

    cursor = conn.cursor()
    try:
        # Verificar se o telefone já existe no banco de clientes
        cursor.execute('SELECT * FROM clientes WHERE telefone = %s', (telefone,))
        if cursor.fetchone():
            st.error("Já existe uma conta com este número de telefone.")
            return

        # Verificar se o usuário já existe no banco de credenciais
        cursor.execute('SELECT * FROM credenciais WHERE usuario = %s', (usuario,))
        if cursor.fetchone():
            st.error("Já existe uma conta com este nome de usuário.")
            return

        # Inserir credenciais
        cursor.execute('INSERT INTO credenciais (usuario, senha) VALUES (%s, %s)', (usuario, senha))

        # Inserir informações pessoais no banco de clientes
        cursor.execute('''INSERT INTO clientes (usuario, nome, telefone, data_nascimento, pais) 
                          VALUES (%s, %s, %s, %s, %s)''',
                       (usuario, nome, telefone, data_nascimento, pais))

        # Obter o ID do cliente recém inserido
        cliente_id = cursor.lastrowid

        # Inserir registro de acesso do cliente
        cursor.execute('INSERT INTO acesso_cliente (cliente_id, bypass, trial_credits) VALUES (%s, %s, %s)',
                       (cliente_id, 0, False))

        conn.commit()
        st.success("Conta criada com sucesso!")


    except Exception as e:
        st.error(f"Erro inesperado: {str(e)}")
    finally:
        cursor.close()
        conn.close()
