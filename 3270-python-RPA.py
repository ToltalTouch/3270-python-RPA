from py3270 import Emulator
import os
import logging
import time
import json

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='mainframe_automation.log'
)

# Constantes - Separe configurações do código
host = 'mainframe.exemplo.gov.br'  # ou IP/host do TN3270
atual_dir = os.path.dirname(os.path.abspath(__file__))
json_file = os.path.join(atual_dir, 'config.json')

def login_data():
    global username, password
    username = input("Digite seu nome de usuário: ")
    password = input("Digite sua senha: ")
    

def connect_to_mainframe():
    """
    Conecta ao mainframe IBM via emulador TN3270
    O emulador traduz os comandos Python para o protocolo TN3270
    """
    try:
        # Cria instância e conecta - visible=True permite ver a interface
        em = Emulator(visible=True)
        logging.info(f"Conectando ao host: {host}")
        em.connect(host)
        return em
    except Exception as e:
        logging.error(f"Erro ao conectar: {str(e)}")
        raise

def login(emulator, username, password):
    """
    Realiza login no sistema do mainframe
    As telas de mainframe geralmente têm campos específicos para isso
    """
    try:
        # Espera a tela carregar - essencial em sistemas mainframe
        emulator.wait_for_field()
        logging.info("Tela inicial carregada")
        
        # Preenche campo de login
        emulator.send_string(username)
        emulator.send_enter()
        logging.info("Nome de usuário enviado")
        
        # Aguarda e preenche campo de senha
        time.sleep(1)  # Pequena espera para o mainframe responder
        emulator.wait_for_field()
        emulator.send_string(password)
        emulator.send_enter()
        logging.info("Senha enviada")
          # Pequena espera para verificar se login foi bem-sucedido
        time.sleep(2)
        
        try:
            status_message = emulator.string_get(24, 1, 40)
            logging.info(f"Mensagem de status: {status_message}")
            
            # Verificando se há mensagem de erro
            if "ACESSO NEGADO" in status_message or "SENHA INVÁLIDA" in status_message:
                logging.error(f"Erro no login: {status_message}")
                return False
                
            # Verificando se há confirmação de login
            if "LOGON ACEITO" in status_message or "BEM-VINDO" in status_message:
                logging.info("Login bem-sucedido!")
        except Exception as e:
            logging.warning(f"Não foi possível ler mensagem de status: {str(e)}")
        
        return True
    except Exception as e:
        logging.error(f"Erro durante login: {str(e)}")
        return False

def navigate_to_system(emulator, system_code):
    """
    Navega para um sistema específico na lista de sistemas disponíveis
    O mainframe mostra uma lista como CGRS, ORYX, SGP, SIMCD, etc.
    """
    try:
        # Aguarda tela com lista de sistemas
        emulator.wait_for_field()
        
        # Envia código do sistema desejado
        logging.info(f"Navegando para sistema: {system_code}")
        emulator.send_string(system_code)
        emulator.send_enter()
        
        # Aguarda carregamento do sistema
        time.sleep(2)
        emulator.wait_for_field()
        
        return True
    except Exception as e:
        logging.error(f"Erro ao navegar para sistema {system_code}: {str(e)}")
        return False

def input_data(emulator):
    """
    Insere dados em um formulário específico
    Cada sistema do mainframe pode ter diferentes telas e campos
    """
    try:
        # Preenche campos da tela do sistema
        logging.info("Inserindo dados no formulário")
        emulator.send_string('123456789')  # CPF, por exemplo
        emulator.send_tab()
        emulator.send_string('01/01/2025')  # Data
        emulator.send_enter()
        
        # Aguarda processamento
        time.sleep(1)
        emulator.wait_for_field()
        
        # Verifica se o processamento foi bem-sucedido usando nossa nova função
        # Ajuste as coordenadas e textos conforme seu sistema específico
        screen_text, success = verify_screen_content(
            emulator, 
            row=24,             # Linha onde mensagens costumam aparecer
            col=1,              # Primeira coluna
            length=50,          # Comprimento suficiente para mensagens
            expected_text="PROCESSADO COM SUCESSO",  # Texto de sucesso
            error_texts=["ERRO", "FALHA", "INVÁLIDO"]  # Textos de erro
        )
        
        if not success:
            logging.error(f"Falha ao processar dados: {screen_text}")
            return False
            
        logging.info("Dados processados com sucesso")
        return True
    except Exception as e:
        logging.error(f"Erro ao inserir dados: {str(e)}")
        return False

def disconnect(emulator):
    """
    Encerra a conexão com o mainframe
    É recomendado usar PF3 ou o comando apropriado para sair dos sistemas
    antes de desconectar
    """
    try:
        # Algumas vezes precisamos sair do sistema antes (PF3 = sair)
        logging.info("Saindo do sistema com PF3")
        emulator.exec_command(b"PF(3)")  # Ou o comando de saída apropriado
        time.sleep(1)
        
        # Fecha conexão
        logging.info("Desconectando do mainframe")
        emulator.disconnect()
        return True
    except Exception as e:
        logging.error(f"Erro ao desconectar: {str(e)}")
        return False

def verify_screen_content(emulator, row, col, length, expected_text=None, error_texts=None):
    """
    Verifica o conteúdo de uma região específica da tela do terminal 3270
    """
    try:
        # Espera a tela estar pronta
        emulator.wait_for_field()
        
        # Lê o texto da posição especificada
        screen_text = emulator.string_get(row, col, length)
        logging.info(f"Texto na posição ({row}, {col}): {screen_text}")
        
        # Se não foram fornecidos parâmetros de verificação, retorna apenas o texto
        if expected_text is None and error_texts is None:
            return screen_text, True
        
        # Verifica se o texto esperado está presente
        if expected_text and expected_text in screen_text:
            logging.info(f"Texto esperado '{expected_text}' encontrado")
            return screen_text, True
        
        # Verifica se algum texto de erro está presente
        if error_texts:
            for error in error_texts:
                if error in screen_text:
                    logging.error(f"Texto de erro '{error}' encontrado")
                    return screen_text, False
        
        # Se tinha texto esperado mas não foi encontrado
        if expected_text:
            logging.warning(f"Texto esperado '{expected_text}' não encontrado")
            return screen_text, False
            
        return screen_text, True
        
    except Exception as e:
        logging.error(f"Erro ao verificar conteúdo da tela: {str(e)}")
        return "", False

def main():
    """
    Função principal que executa a sequência de automação
    """
    global username, password
    login_data()
    emulator = None
    try:
        # Estabelece conexão
        emulator = connect_to_mainframe()
        
        # Realiza login
        if not login(emulator, username, password):
            logging.error("Falha no login. Abortando.")
            return
        
        # Navega para o sistema desejado
        if not navigate_to_system(emulator, system_code):
            logging.error("Falha ao navegar para o sistema. Abortando.")
            return
        
        # Insere dados no sistema
        if not input_data(emulator):
            logging.error("Falha ao inserir dados. Abortando.")
            return
        
        logging.info("Automação concluída com sucesso!")
    
    except Exception as e:
        logging.error(f"Erro inesperado: {str(e)}")
    
    finally:
        # Garante que a conexão seja fechada mesmo em caso de erro
        if emulator:
            disconnect(emulator)

if __name__ == "__main__":
    main()