from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import logging
import time
from typing import Optional, Tuple, List
from contextlib import contextmanager

from config import AppConfig
from credential_manager import CredentialManager

class DownloadTerminal:
    def __init__(self, config: AppConfig = None):
        self.config = config or AppConfig()
        self.credential_manager = CredentialManager()
        self.driver = None
        self.wait = None
        
        self.setup_webdriver()
        self.setup_logging()
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            filename=self.config.log_file,
            filemode='a'
        )        
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        self.logging = logging.getLogger().addHandler(console_handler)
        
    def setup_webdriver(self):
        try:
            if not os.path.exists(self.config.edge_path):
                raise FileNotFoundError(f"WebDriver não encontrado em {self.config.edge_path}")
            
            service = Service(self.config.edge_path)
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            
            self.driver = webdriver.Edge(service=service, options=options)
            self.wait = WebDriverWait(self.driver, self.config.ELEMENT_WAIT_TIMEOUT)
            
            return self.driver
            
        except Exception as e:
            logging.error(f"Erro ao configurar o WebDriver: {str(e)}")
            raise
        
    def wait_for_download(self) -> Optional[str]:
        start_time = time.time()
        initial_files = set()
        timeout = self.config.DEFAULT_TIMEOUT
        
        while time.time() - start_time < timeout:
            if os.path.exists(self.config.download_dir):
                current_files = {f for f in os.listdir(self.config.download_dir) if f.endswith('.jsp')}
                new_files = current_files - initial_files
                
                if new_files:
                    newest_file = max([os.path.join(self.config.download_dir, f) for f in current_files], key=os.path.getmtime)
                    logging.info(f"Novo arquivo deectado: {newest_file}")
                    return newest_file
                
                logging.info(f"Arquivos encontrados no diretório de download: {current_files}")
                
            time.sleep(1)
            
        logging.info(f"Timeout de {timeout} segundos atingido sem novos downloads.")
        return None
    
    def _check_login_erros(self) -> Tuple[bool, List[str]]:
        try:
            erros_xpath = [
                    "//span[@class='mensagem' and contains(text(), 'Senha nao confere')]",
                    "//span[@class='mensagem' and contains(text(), 'Usuário não cadastrado')]",
                    "//span[@class='mensagem']"
            ]
            
            errors_message = []
            for xpath in erros_xpath:
                try:
                    elements = self.driver.find_elements(By.XPATH, xpath)
                    for element in elements:
                        if element.is_displayed():
                            errors_message.append(element.text)
                except:
                    continue
            return len(errors_message) > 0, errors_message
        except Exception as e:
            logging.error(f"Erro ao verificar erros de login: {str(e)}")
            return False, []
        
    def download_3270_terminal(self, username: str = None, password: str = None) -> Optional[str]:
        self.driver.get(self.config.HOST)
        
        for retry_attempt in range(self.config.MAX_RETRIES +1):
            try:
                if retry_attempt > 0:
                    logging.info(f"Tentativa {retry_attempt + 1} de download do terminal 3270.")
                    self.driver.get(self.config.HOST)
                    time.sleep(2)
                    
                username, password = self.credential_manager.get_credentials(
                    username, password, retry_attempt
                    )
                
                if not username or not password:
                    logging.error("Credenciais não fornecidas.")
                    continue
                
                logging.info(f"Tentativa {retry_attempt + 1} de login.")
                
                self.wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="login_user"]'))).send_keys(username)
                self.wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="login_password"]'))).send_keys(password)
                
                self.driver.find_element(By.XPATH, '//*[@id="login_button"]').click()
                
                time.sleep(1)
                
                has_error, error_messages = self._check_login_erros()
                
                if has_error:
                    logging.error(f"Erro de login Tentativa {retry_attempt + 1}")
                    for msg in error_messages:
                        logging.error(f"Mensagem de erro: {msg}")
                    
                    else:
                        logging.error("Máximo de tentativas atingido.")
                        return None
                
                download_file = self.wait_for_download()
                return download_file
            
            except TimeoutException:
                logging.error(f"Tempo limite excedido na tentativa {retry_attempt + 1}.")
                try:
                    self.driver.get(self.config.HOST)
                except Exception as e:
                    logging.error(f"Erro ao recarregar a página: {str(e)}")
                continue
        
        logging.error("Falha em todas as tentativas de download do terminal 3270.")
        return None
                