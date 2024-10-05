from datetime import datetime
import mysql.connector
import time

def verificar_login(controller, usuario, senha):
    print(f'Logged_In Verificar Login: {controller.get('logged_in')}')
    print(f'Cliente Verificar Login: {controller.get('cliente_id')}')
    conn = mysql.connector.connect(
        host='geniusfut.c7k02g0my0as.us-east-2.rds.amazonaws.com',
        user='renaneunao',
        password='*Vitorya111',
        database='geniusfut_database',
        port=3306
    )

    cursor = conn.cursor()
    cursor.execute('SELECT id FROM credenciais WHERE usuario = %s AND senha = %s', (usuario, senha))
    data = cursor.fetchone()
    conn.close()

    return data  # Retorna apenas o id


def verificar_acesso(controller, cliente_id):
    print(f'Logged_In Verificar Acesso: {controller.get('logged_in')}')
    print(f'Cliente Verificar Acesso: {controller.get('cliente_id')}')
    conn = mysql.connector.connect(
        host='geniusfut.c7k02g0my0as.us-east-2.rds.amazonaws.com',
        user='renaneunao',
        password='*Vitorya111',
        database='geniusfut_database',
        port=3306
    )
    cursor = conn.cursor()
    cursor.execute('SELECT data_limite, bypass FROM acesso_cliente WHERE cliente_id = %s', (cliente_id,))
    data = cursor.fetchone()
    conn.close()

    if data:
        data_limite, bypass = data
        hoje = datetime.now().date()

        # Verifica se data_limite é uma string antes de tentar converter
        if isinstance(data_limite, str):
            data_limite = datetime.strptime(data_limite, "%Y-%m-%d").date()  # Converte string para date

        # Agora você pode comparar diretamente
        if bypass or data_limite >= hoje:
            return True
        else:
            return False
    return False


def login(st, controller):
    controller.set('logged_in', False)  # Remover o estado de login
    controller.set('cliente_id', False)  # Opcional: limpar o cliente_id
    print(f'Logged_In Main: {controller.get('logged_in')}')
    print(f'Cliente Main: {controller.get('cliente_id')}')
    # Verifica se o usuário está logado
    logged_in = controller.get('logged_in')
    cliente_id = controller.get('logged_in')

    while logged_in is None:
        logged_in = controller.get('logged_in')
        # Pausa para evitar sobrecarga no processamento
        time.sleep(1)  # Aguarda 1 segundo antes de verificar novamente
        # st.write('Aguarde. Carregando inicialização')
    while cliente_id is None:
        logged_in = controller.get('cliente_id')
        # Pausa para evitar sobrecarga no processamento
        time.sleep(1)  # Aguarda 1 segundo antes de verificar novamente
        # st.write('Aguarde. Carregando especificações do cliente')

    st.title("Login")
    usuario = st.text_input("Usuário", key='text_input_usuario_login')
    senha = st.text_input("Senha", type='password', key='text_input_password_login')

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Entrar"):
            credenciais = verificar_login(controller, usuario, senha)
            if credenciais:
                conn = mysql.connector.connect(
                    host='geniusfut.c7k02g0my0as.us-east-2.rds.amazonaws.com',
                    user='renaneunao',
                    password='*Vitorya111',
                    database='geniusfut_database',
                    port=3306
                )

                cursor_clientes = conn.cursor()
                cursor_clientes.execute('SELECT id FROM clientes WHERE usuario = %s', (usuario,))
                cliente = cursor_clientes.fetchone()

                if cliente:
                    cliente_id = cliente[0]
                    cursor_acessos = conn.cursor()
                    cursor_acessos.execute('SELECT data_limite, bypass FROM acesso_cliente WHERE cliente_id = %s',
                                           (cliente_id,))
                    acesso = cursor_acessos.fetchone()

                    conn.close()  # Fechar a conexão após obter os dados

                    if acesso:
                        data_limite, bypass = acesso
                        controller.set('data_limite',
                                       data_limite.strftime('%Y-%m-%d'))  # Converter para string no formato ISO

                        controller.set('bypass', bypass)

                        # Verificar se a data limite é menor que hoje e o bypass é zero
                        if data_limite < datetime.now().date() and bypass == 0:
                            st.error("Acesso negado. É necessário comprar uma licença.")
                        else:
                            if verificar_acesso(controller, cliente_id):
                                st.success("Login bem-sucedido! Bem-vindo à tela principal.")

                                # Armazena os cookies
                                controller.set('logged_in', True)
                                controller.set('cliente_id', cliente_id)
                                # main()
                                st.rerun()
                            else:
                                st.error("Acesso negado. Verifique a data limite ou contate o suporte.")
                    else:
                        st.error("Nenhum acesso encontrado para este cliente.")
                else:
                    st.error("Cliente não encontrado.")
            else:
                st.error("Usuário ou senha incorretos.")

    with col2:
        # Botão para ir à tela de criar nova conta
        if st.button("Criar nova conta"):
            st.session_state['screen'] = 'criar_conta'  # Muda a tela para criação de conta
            st.rerun()