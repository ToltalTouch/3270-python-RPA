from pywinauto.application import ProcessNotFoundError
from pywinauto.application import Application
from contextlib import contextmanager
from typing import Optional
import logging
import time
import os

# chamando arquivos de configuração, gerenciamento de cerencias, e download de terminal
from app.credential_manager import CredentialManager
from app.download_terminal import DownloadTerminal
from app.config import AppConfig, setup_logging
from app.rpa_3270 import Mainframe3270Automation

class Open3270file:
    # configuração inicial
    def __init__(self, config: AppConfig = None):
        self.config = config or AppConfig()
        # Configura logging uma única vez na classe principal
        self.logger = setup_logging(self.config.log_file)
        
        self.credential_manager = CredentialManager()
        self.download = DownloadTerminal()
        self.reconhecer_terminal = Mainframe3270Automation(self.config, self.download)
    
    # exclusao de arquivo temporario
    @contextmanager
    def _safe_file_operation(self, file_path: str):
        try:
            yield file_path
        finally:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logging.info(f"Arquivo temporario removido: {file_path}")
                except Exception as e:
                    logging.error(f"Erro ao remover arquivo temporario {file_path}: {str(e)}")
    
    # validação do caminho do arquivo                
    def _validate_file_path(self, file_path: str) -> bool:
        if not file_path or not os.path.exists(file_path):
            logging.error(f"Arquivo não encontrado: {file_path}")    
            return False
        
        return True
    
    # identificação da janela de segurança e fechamento
    def security_check(self) -> bool:
        try:
            for pattern in self.config.SECURITY_WARNING_PATTERNS:
                
                logging.info("Procurando janela de segurança")
                    # identifica a janela pelo nome padrao presente no arquivo config.py
                app = Application(backend="win32").connect(
                    title_re=pattern,
                    timeout=self.config.SECURITY_CHECK_TIMEOUT
                )
                    # definindo a janela
                dlg = app.window(title_re=pattern)
                    
                    # verifica se a janela existe
                if dlg.exists():
                        # preciona a sequencia de botões para fechar a janela
                        dlg.type_keys("{TAB}" * 2 + "{ENTER}", pause=0.1)
                        logging.info("Janela de segurança fechada com sucesso")
                        return True
                     
        except Exception as e:
            logging.error(f"Erro na verificação de segurança: {str(e)}")
            return False
    
    # lê o arquivo com o encondig correto
    def _read_file_content(self, file_path: str) -> Optional[str]:        
        for encoding in ['utf-8']:
            try:
                with open(file_path, 'r', encoding=encoding) as file:
                    content = file.read()
                    logging.info(f"Conteúdo lido do arquivo {file_path} com codificação {encoding}")
                    return content
            except (UnicodeDecodeError, Exception) as e:
                logging.error(f"Erro ao ler arquivo {file_path} com codificação {encoding}: {str(e)}")
                continue
        
        logging.error(f"Não foi possível ler o arquivo {file_path} com nenhuma das codificações tentadas")
        return None
    
    # abre o emulador 3270
    def open_3270_emulator(self, file_path: str) -> bool:
        try:
            if not self._validate_file_path(file_path):
                return False
            content = self._read_file_content(file_path)
            if not content:
                logging.error(f"Conteúdo do arquivo {file_path} não pôde ser lido")
                return False
            
            # pelo nome do arquivo identifica o arquivo correto na pasta de downloads
            if "hodcivws" in content:
                logging.info("Emulador 3270 encontrado no arquivo.")
                try:
                    # pelo url do arquivo, abre o emulador no navegador
                    file_url = f"file:///{file_path.replace(os.sep, '/')}"
                    os.startfile(file_url)

                except Exception as e:
                    logging.error(f"Erro ao abrir o arquivo no navegador: {e}")
                    return False             
                return True
                
        except Exception as e:
            logging.error(f"Erro ao processar o arquivo {os.path.basename(file_path) if file_path else 'desconhecido'}: {str(e)}")
            return False
    
    def establish_3270_connection(self) -> bool:
        logging.info("Iniciando processo de conexão com terminal 3270")
        
        downloaded_file = self.download.download_3270_terminal()
        if not downloaded_file:
            logging.error("Falha no download do emulador 3270")
            return False
        
        with self._safe_file_operation(downloaded_file) as file_path:
            if not self.open_3270_emulator(file_path):
                logging.error("Falha ao abrir emulador 3270")
                return False
            
            self.security_check()

            self.reconhecer_terminal.reconhecer_janela()
    
    def run(self):
        try:
            logging.info("Iniciando automação do mainframe")

            self.driver = self.download.setup_webdriver()
            self.driver.get(self.config.HOST)
            time.sleep(3)
            
            try:
                self.establish_3270_connection()
            except Exception as e:
                logging.error(f"Erro ao estabelecer conexão com o terminal 3270: {str(e)}")
                
        except Exception as e:
            logging.error(f"Erro durante execução: {e}")
        finally:
            self.cleanup()

    def cleanup(self):
        try:
            if self.driver:
                self.driver.quit()
                logging.info("WebDriver encerrado")
        except Exception as e:
            logging.error(f"Erro durante limpeza: {e}")