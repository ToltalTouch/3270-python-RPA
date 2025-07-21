from pywinauto.application import Application
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
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
                    except Exception as key_error:
                        logging.debug(f"Erro ao enviar tecla: {key_error}")
                    
            except Exception as pattern_error:
                logging.debug(f"Padrão {pattern} não encontrado: {pattern_error}")
                continue
        
    except Exception as e:
        logging.error(f"Erro ao verificar a advertência de segurança: {str(e)}")
        return False

def recognize_3270_emulator():
    terminal_patterns = [".*Terminal 3270.*"]
        
    for pattern in terminal_patterns:
        try:
            logging.info(f"Procurando terminal com padrão: {pattern}")
            terminal_app = Application(backend="win32").connect(title_re=pattern, timeout=10)
            terminal_dlg = terminal_app.window(title_re=pattern)
            if terminal_dlg.exists():
                logging.info(f"Terminal 3270 encontrado com padrão: {pattern}")
                return True
        except Exception as terminal_error:
            logging.debug(f"Terminal não encontrado com padrão {pattern}: {terminal_error}")
            continue

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
                logging.info(f"Abrindo arquivo JSP no navegador: {file_url}")
                os.startfile(file_url)
                logging.info(f"Arquivo JSP aberto no navegador: {file_path}")
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

def download_3270_emulator(password=None, username=None):
    try:
        wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="login_user"]'))).send_keys(username)
        wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="login_password"]'))).send_keys(password)
        driver.find_element(By.XPATH, '//*[@id="login_button"]').click()
        logging.info("Tentando efetuar download do emulador 3270.")
        time.sleep(3)

        new_file = wait_for_download(download_dir)
        if new_file:
            logging.info(f"Arquivo baixado: {new_file}")
            driver.quit()
            return new_file  # Retorna o caminho do arquivo baixado
        else:
            logging.info("Nenhum arquivo baixado encontrado.")
            driver.quit()
            return None

    except Exception as e:
        logging.error(f"Erro ao acessar o site: {str(e)}")
        driver.quit()
        return None

def main():
    global password, username
    driver.get(host)
    logging.info(f"Diretório de downloads: {download_dir}")

    while True:
        try:
            username = input("Digite seu usuario (CPF): ")
            if len(username) <= 12:
                break
            logging.error("Usuário inválido")
        except Exception as e:
            logging.error(f"Erro ao obter usuário: {str(e)}")

    password = getpass.getpass("Digite sua senha: ")

    logging.info("Credenciais recebidas com sucesso.")
    time.sleep(3)
    logging.info("Iniciando o processo de download do emulador 3270.")
    wait.until(EC.presence_of_element_located((By.XPATH, '/html/body')))
    
    new_file = download_3270_emulator(password=password, username=username)
    if new_file:
        if open_3270_emulator(file_path=new_file):
            if security_check():
                logging.info("Conexão com o emulador 3270 estabelecida com sucesso.")
                if recognize_3270_emulator():
                    logging.info("Emulador 3270 reconhecido com sucesso.")
                    os.remove(new_file)
                else:
                    logging.error("Emulador 3270 não reconhecido.")
            else:
                logging.error("Falha ao estabelecer conexão com o emulador 3270.")
        else:
            logging.error("Falha ao abrir o emulador 3270.")
            os.remove(new_file)
    else:
        logging.error("Falha no download do emulador 3270.")

if __name__ == "__main__":
    main()