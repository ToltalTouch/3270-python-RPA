from py3270 import Emulator
import os
import logging
import time
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='mainframe_automation.log'
)

host = 'mainframe.exemplo.gov.br'
atual_dir = os.path.dirname(os.path.abspath(__file__))
json_file = os.path.join(atual_dir, 'config.json')

sistema = None

def login_data():
    global username, password
    username = input("Digite seu nome de usuário: ")
    password = input("Digite sua senha: ")
    

def connect_to_mainframe():
    try:
        em = Emulator(visible=True)
        logging.info(f"Conectando ao host: {host}")
        em.connect(host)
        return em
    except Exception as e:
        logging.error(f"Erro ao conectar: {str(e)}")
        raise

def login(emulator, username, password):
    try:

        emulator.wait_for_field()
        logging.info("Tela inicial carregada")
        
        # Preenche campo de login
        emulator.send_string(username)
        emulator.send_enter()
        logging.info("Nome de usuário enviado")
        
        time.sleep(1) 
        emulator.wait_for_field()
        emulator.send_string(password)
        emulator.send_enter()
        logging.info("Senha enviada")

        time.sleep(2)
        
        try:
            status_message = emulator.string_get(24, 1, 40)
            logging.info(f"Mensagem de status: {status_message}")
            
            if "ACESSO NEGADO" in status_message or "SENHA INVÁLIDA" in status_message:
                logging.error(f"Erro no login: {status_message}")
                return False
                
            if "LOGON ACEITO" in status_message or "BEM-VINDO" in status_message:
                logging.info("Login bem-sucedido!")
        except Exception as e:
            logging.warning(f"Não foi possível ler mensagem de status: {str(e)}")
        
        return True
    except Exception as e:
        logging.error(f"Erro durante login: {str(e)}")
        return False

def navigate_to_system(emulator, system_code):
    try:
        emulator.wait_for_field()
        
        logging.info(f"Navegando para sistema: {system_code}")
        emulator.send_string(system_code)
        emulator.send_enter()
        
        time.sleep(2)
        emulator.wait_for_field()
        
        return True
    except Exception as e:
        logging.error(f"Erro ao navegar para sistema {system_code}: {str(e)}")
        return False

def input_data(emulator):
    try:
        logging.info("Inserindo dados no formulário")
        emulator.send_string('123456789')
        emulator.send_tab()
        emulator.send_string('01/01/2025')
        emulator.send_enter()
        
        time.sleep(1)
        emulator.wait_for_field()
        
        screen_text, success = verify_screen_content(
            emulator,
            row=24,
            col=1,
            length=50,
            expected_text="PROCESSADO COM SUCESSO",
            error_texts=["ERRO", "FALHA", "INVÁLIDO"]
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
    try:
        logging.info("Saindo do sistema com PF3")
        emulator.exec_command(b"PF(3)")
        time.sleep(1)
        
        logging.info("Desconectando do mainframe")
        emulator.disconnect()
        return True
    except Exception as e:
        logging.error(f"Erro ao desconectar: {str(e)}")
        return False

def verify_screen_content(emulator, row, col, length, expected_text=None, error_texts=None):
    try:
        emulator.wait_for_field()
        
        screen_text = emulator.string_get(row, col, length)
        logging.info(f"Texto na posição ({row}, {col}): {screen_text}")
        
        if expected_text is None and error_texts is None:
            return screen_text, True
        
        if expected_text and expected_text in screen_text:
            logging.info(f"Texto esperado '{expected_text}' encontrado")
            return screen_text, True
        
        if error_texts:
            for error in error_texts:
                if error in screen_text:
                    logging.error(f"Texto de erro '{error}' encontrado")
                    return screen_text, False
        
        if expected_text:
            logging.warning(f"Texto esperado '{expected_text}' não encontrado")
            return screen_text, False
            
        return screen_text, True
        
    except Exception as e:
        logging.error(f"Erro ao verificar conteúdo da tela: {str(e)}")
        return "", False

def main():
    global username, password
    login_data()
    emulator = None
    try:
        emulator = connect_to_mainframe()
        
        if not login(emulator, username, password):
            logging.error("Falha no login. Abortando.")
            return
        
        if not navigate_to_system(emulator, sistema):
            logging.error("Falha ao navegar para o sistema. Abortando.")
            return
        
        if not input_data(emulator):
            logging.error("Falha ao inserir dados. Abortando.")
            return
        
        logging.info("Automação concluída com sucesso!")
    
    except Exception as e:
        logging.error(f"Erro inesperado: {str(e)}")
    
    finally:
        if emulator:
            disconnect(emulator)

if __name__ == "__main__":
    main()