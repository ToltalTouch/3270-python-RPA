from pywinauto.application import Application
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from py3270 import Emulator
import getpass
import os
import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='mainframe_automation.log'
)

logging.getLogger().addHandler(logging.StreamHandler())

host = r'https://hod.serpro.gov.br/a83016cv/'
atual_dir = os.path.dirname(os.path.abspath(__file__))

userpath = os.getlogin()

download_dir = f"C:\\Users\\{userpath}\\Downloads"
edge_path = os.path.join(atual_dir, "edgedriver_win64", "msedgedriver.exe")

webdriver_service = Service(executable_path=edge_path)
edge_options = Options()
edge_options.add_argument("--headless")
driver = webdriver.Edge(service=webdriver_service, options=edge_options)

wait = WebDriverWait(driver, 260)

saved_user = None
saved_password = None

def security_check():
    try:
        title_patterns = [".*Advertência de Segurança.*"]
        for pattern in title_patterns:
            try:
                logging.info(f"Tentando conectar com padrão: {pattern}")
                app = Application(backend="win32").connect(title_re=pattern, timeout=15)
                dlg = app.window(title_re=pattern)
                
                if dlg.exists():
                    logging.info(f"Janela encontrada com padrão: {pattern}")
       
                    try:
                        logging.info("Tentando simular tecla Enter.")
                        dlg.type_keys("{TAB}" * 2 + "{ENTER}", pause=0.5)
                        logging.info("Tecla ENTER enviada com sucesso.")
                        return True
                    except Exception as key_error:
                        logging.debug(f"Erro ao enviar tecla: {key_error}")
                    
            except Exception as pattern_error:
                logging.debug(f"Padrão {pattern} não encontrado: {pattern_error}")
                continue
        
    except Exception as e:
        logging.error(f"Erro ao verificar a advertência de segurança: {str(e)}")
        return False

def recognize_3270_emulator(timeout=40):
    start_time = time.time()
    terminal_patterns = [".*Terminal 3270.*"]

    while time.time() - start_time < timeout:
        try:
            for pattern in terminal_patterns:
                try:
                    logging.info(f"Procurando terminal com padrão: {pattern}")
                    terminal_app = Application(backend="win32").connect(title_re=pattern, timeout=5)
                    terminal_dlg = terminal_app.window(title_re=pattern)
                    
                    if terminal_dlg.exists():
                        terminal_dlg.wait("exists", timeout=5)
                        terminal_dlg.wait("visible", timeout=5)
                        
                        logging.info(f"Terminal 3270 encontrado e visível com padrão: {pattern}")
                        return True
                        
                except Exception as terminal_error:
                    logging.debug(f"Terminal não encontrado com padrão {pattern}: {terminal_error}")
                    continue
            
            logging.info(f"Aguardando terminal aparecer... {int(timeout - (time.time() - start_time))}s restantes")
            time.sleep(2)
            
        except Exception as e:
            logging.error(f"Erro ao reconhecer o emulador 3270: {str(e)}")
            time.sleep(2)
    
    logging.warning(f"Terminal 3270 não encontrado após {timeout} segundos.")
    return False

def open_3270_emulator(file_path=None):
    try:
        content = None    
        for encoding in ['utf-8']:
            try:
                with open(file_path, 'r', encoding=encoding) as file:
                    content = file.read()
                    logging.info(f"Arquivo lido com codificação: {encoding}")
                    break
            except UnicodeDecodeError:
                continue
        
        if "hodcivws" in content:
            logging.info("Emulador 3270 encontrado no arquivo.")
            try:
                file_url = f"file:///{file_path.replace(os.sep, '/')}"
                os.startfile(file_url)

            except Exception as e:
                logging.error(f"Erro ao abrir o arquivo no navegador: {e}")
                return False
            
            return True
            
    except Exception as e:
        logging.error(f"Erro ao processar o arquivo {os.path.basename(file_path) if file_path else 'desconhecido'}: {str(e)}")
        return False

def wait_for_download(download_dir, timeout=60):
    start_time = time.time()
    initial_files = set()
    
    while time.time() - start_time < timeout:
        if os.path.exists(download_dir):
            current_files = {f for f in os.listdir(download_dir) if f.endswith('.jsp')}
            new_files = current_files - initial_files
            
            if new_files:
                newest_file = max([os.path.join(download_dir, f) for f in current_files], key=os.path.getmtime)
                logging.info(f"Novo arquivo detectado: {newest_file}")
                return newest_file
            
            logging.info(f"Arquivos encontrados no diretório de downloads: {current_files}")
        
        time.sleep(1)
    
    logging.info(f"Timeout de {timeout} segundos atingido. Nenhum arquivo novo encontrado.")
    return None

def download_3270_emulator(password=None, username=None, max_retries=3):
    retry_attempt = 0
    
    while retry_attempt < max_retries:
        try:
            if retry_attempt > 0:
                logging.info(f"Recarregando página para tentativa {retry_attempt + 1}...")
                driver.get(host)
                wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="login_user"]')))
                time.sleep(2)
            
            username, password = get_credentials(username, password, retry_attempt)

            logging.info(f"Tentativa {retry_attempt + 1} - Acessando o site para download do emulador 3270.")

            wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="login_user"]'))).send_keys(username)
            wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="login_password"]'))).send_keys(password)

            driver.find_element(By.XPATH, '//*[@id="login_button"]').click()
            logging.info("Tentando efetuar login do emulador 3270.")

            has_error, error_messages = check_login_errors()
            
            if has_error:
                logging.error(f"Erro de credenciais na tentativa {retry_attempt + 1}:")
                for msg in error_messages:
                    logging.error(f"  - {msg}")
                
                retry_attempt += 1
                
                if retry_attempt < max_retries:
                    logging.info(f"Tentando novamente... ({retry_attempt + 1}/{max_retries})")
                    username = None
                    password = None
                    continue
                else:
                    logging.error(f"Máximo de tentativas ({max_retries}) atingido. Encerrando.")
                    return None
            logging.info("Login realizado com sucesso!")

        except TimeoutException:
            try:
                error_element = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="mensagem"]/p[2]/span')))
                error_message = error_element.text
                logging.error(f"Erro ao efetuar Login: {error_message}")
                try:
                    driver.get(host)
                except Exception as e:
                    logging.error(f"Erro ao tentar recarregar a página: {str(e)}")
            except Exception as e:
                logging.error(f"Erro ao localizar mensagem de erro: {str(e)}")
                return None
            
        new_file = wait_for_download(download_dir)
        if not new_file:
            logging.info("Nenhum arquivo baixado encontrado.")
            return None
        return new_file

def check_login_errors():
    try:
        error_xpaths = [
            "//span[@class='mensagem' and contains(text(), 'Senha nao confere')]",
            "//span[@class='mensagem' and contains(text(), 'Usuário não cadastrado')]",
            "//span[@class='mensagem']"
        ]
        
        error_messages = []
        for xpath in error_xpaths:
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                for element in elements:
                    if element.is_displayed() and element.text.strip():
                        error_messages.append(element.text.strip())
            except:
                continue
        
        return len(error_messages) > 0, error_messages
        
    except Exception as e:
        logging.debug(f"Erro ao verificar mensagens de erro: {e}")
        return False, []
    
def get_credentials(username=None, password=None, retry_attempt=0):
    try:
        username = username or saved_user
        password = password or saved_password
        if retry_attempt == 0:
            logging.info("Obtendo credenciais...")
        else:
            logging.info(f"Tentativa {retry_attempt + 1} - Digite novas credenciais:")

        if username is None or retry_attempt > 0:
            username = input("Digite o usuario (CPF): ")
            saved_user = username
        
        if password is None or retry_attempt > 0:
            password = getpass.getpass("Digite a senha: ")
            saved_password = password

        return username, password
    
    except Exception as e:
        logging.error(f"Erro ao obter credenciais: {str(e)}")
        return None, None

def check_3270_connection():
    try:
        em = Emulator(visible=True)
        screen_content = em.string_get(1, 1, 80, 24)
        non_empty_lines = [line.strip() for line in screen_content.split('\n') if line.strip()]
        if len(non_empty_lines) <= 3:
            logging.info("Conexão com o 3270 foi perdida")

            disconnection_indicators = [
                "MA?",
                "Desconectado",
                "659",
                "/001"
            ]

            screen_lower = screen_content.lower()
            disconnected = any(indicator.lower() in screen_lower for indicator in disconnection_indicators)

            if disconnected:
                logging.info("Conexão com o 3270 foi perdida.")
                open_3270_file()
                return True
            
        else:
            connected_indicators = [
                "MENU DE SISTEMA",
                "CODIGO",
                "USUARIO",
                "PF3",
                "PF7"
            ]

            is_connected = any(indicator in screen_content for indicator in connected_indicators)

            if is_connected:
                logging.info("Conexão com o 3270 está ativa.")
                return False
            else:
                logging.info("Conexão com o 3270 não está ativa, tentando reconectar.")
                open_3270_file()
                return True
            
    except Exception as e:
        logging.error(f"Erro ao verificar conexão com o 3270: {str(e)}")
        logging.error(f"Assumindo deconexaão com o 3270 - Reabrindo o emulador")
        open_3270_file()
        return True

def open_3270_file():
    global saved_user, saved_password
    logging.info("Iniciando processo de conexão como terminal 3270")
    new_file = download_3270_emulator()
    try:
        if new_file:
            if open_3270_emulator(file_path=new_file):
                if security_check():
                    logging.info("Conexão com o emulador 3270 estabelecida com sucesso.")
                    time.sleep(5)
                    if recognize_3270_emulator():
                        logging.info("Emulador 3270 reconhecido com sucesso.")
                        time.sleep(5)
                        os.remove(new_file)
                        return True
                    else:
                        logging.error("Falha ao reconhecer o emulador 3270.")
                        os.remove(new_file)
                        return False
                else:
                    logging.error("Falha ao estabelecer conexão com o emulador 3270.")
                    os.remove(new_file)
                    return False
            else:
                logging.error("Falha ao abrir o emulador 3270.")
                os.remove(new_file)
                return False
        else:
            logging.error("Falha no download do emulador 3270.")
            return False
    except Exception as e:
        logging.error(f"Erro ao abrir o emulador 3270: {str(e)}")
        if new_file and os.path.exists(new_file):
            os.remove(new_file)

def monitor_3270_connection(check_interval=20):
    while True:
        try:
            is_disconnected = check_3270_connection()
            if is_disconnected:
                logging.info("Processos de reconexão conluído.")
            else:
                logging.info("Conexão com o 3270 está ativa.")

            time.sleep(check_interval)
        except Exception as e:
            logging.error(f"Erro durante o monitoramento da conexão 3270: {str(e)}")
            time.sleep(check_interval)
        except KeyboardInterrupt:
            logging.info("Monitoramento interrompido pelo usuário.")
            break

def main():
    global saved_user, saved_password

    driver.get(host)
    time.sleep(3)

    new_file = download_3270_emulator()
    if new_file:
        if open_3270_emulator(file_path=new_file):
            if security_check():
                logging.info("Conexão com o emulador 3270 estabelecida com sucesso.")
                time.sleep(5)
                if recognize_3270_emulator():
                    logging.info("Emulador 3270 reconhecido com sucesso.")
                    time.sleep(5)
                    os.remove(new_file)
                    monitor_3270_connection()
                else:
                    logging.error("Falha ao reconhecer o emulador 3270.")
                    os.remove(new_file)
            else:
                logging.error("Falha ao estabelecer conexão com o emulador 3270.")
                os.remove(new_file)
        else:
            logging.error("Falha ao abrir o emulador 3270.")
            os.remove(new_file)

if __name__ == "__main__":
    main()