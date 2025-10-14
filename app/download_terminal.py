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

from app.config import AppConfig
from app.credential_manager import CredentialManager

class DownloadTerminal:
    def __init__(self, config: AppConfig = None):
        self.config = config or AppConfig()
        self.credential_manager = CredentialManager()
        self.driver = None
        self.wait = None
        self.stored_token = None  # Armazena o token detectado durante o login
        # Não configura logging aqui - será configurado na classe principal
        
    def setup_webdriver(self):
        try:
            if not os.path.exists(self.config.edge_path):
                raise FileNotFoundError(f"WebDriver não encontrado em {self.config.edge_path}")
            
            service = Service(self.config.edge_path)
            options = Options()
            options.add_argument("--headless")#maximized
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
                    logging.info(f"Novo arquivo detectado: {newest_file}")
                    return newest_file
                
                logging.info(f"Arquivos encontrados no diretório de download: {current_files}")
                
            time.sleep(1)
            
        logging.info(f"Timeout de {timeout} segundos atingido sem novos downloads.")
        return None
        
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
                time.sleep(1.5)
                token = self.driver.find_element(By.XPATH, '//*[@id="mensagem"]/p[3]/span/button')
                if token:
                    logging.info("Token solicitado com sucesso.")
                    token.click()

                has_token, token_message = self._check_login_token()

                if has_token:
                    for msg in token_message:
                        logging.error(f"Token encontrado: {msg}")
                    # Armazena o token para uso posterior no terminal
                    self.stored_token = token_message
                    logging.info("Token armazenado para inserção no terminal 3270")
                
                # Aguarda o download independentemente se há token ou não
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
                
    def _check_login_token(self) -> Tuple[bool, List[str]]:
        try:
            import re
            
            # XPath patterns para diferentes tipos de mensagens
            token_xpath = [
                "//span[@class='mensagem' and contains(text(), 'Senha nao confere')]",
                "//span[@class='mensagem' and contains(text(), 'Usuário não cadastrado')]",
                "//span[@class='mensagem']",
            ]
            
            token_message = []
            for xpath in token_xpath:
                try:
                    elements = self.driver.find_elements(By.XPATH, xpath)
                    for element in elements:
                        if element.is_displayed():
                            text = element.text.strip()
                            if text:
                                # Verifica se há números no texto (possível token)
                                numbers = re.findall(r'\d+', text)
                                if numbers:
                                    # Se encontrou números, adiciona o texto completo
                                    token_message.append(text)
                                    logging.info(f"Possível token detectado: {text}")
                                elif any(keyword in text.lower() for keyword in ['senha', 'usuário', 'erro', 'token']):
                                    # Se é uma mensagem de erro conhecida, também adiciona
                                    token_message.append(text)
                                    logging.info(f"Mensagem de sistema detectada: {text}")
                except Exception as xpath_error:
                    logging.debug(f"Erro ao processar xpath {xpath}: {xpath_error}")
                    continue
            
            # Se encontrou mensagens, retorna True
            if token_message:
                return True, token_message
            
            # Se nenhuma mensagem foi encontrada, retorna False
            return False, []
                
        except Exception as e:
            logging.error(f"Erro ao verificar token: {str(e)}")
            return False, []
    
    def get_stored_token(self) -> Tuple[bool, List[str]]:
        """
        Retorna o token armazenado durante o processo de login.
        
        Returns:
            Tuple[bool, List[str]]: (tem_token, lista_de_tokens)
        """
        if self.stored_token:
            return True, self.stored_token
        return False, []
    
    def _driverquit(self):
        if self.driver:
            try:
                self.driver.quit()
                logging.info("WebDriver encerrado com sucesso.")
            except Exception as e:
                logging.error(f"Erro ao encerrar o WebDriver: {str(e)}")
        else:
            logging.warning("WebDriver já está encerrado ou não foi inicializado.")
        return self._driverquit()