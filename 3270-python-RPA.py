from pywinauto.application import Application
from pywinauto.application import ProcessNotFoundError
from py3270 import Emulator
import os
import logging
import time
from typing import Optional
from contextlib import contextmanager

from config import AppConfig
from credential_manager import CredentialManager
from download_terminal import DownloadTerminal

class Mainframe3270Automation:
    def __init__(self, config: AppConfig = None):
        self.config = config or AppConfig()
        self.credential_manager = CredentialManager()
        self.download = DownloadTerminal()
        self.driver = None
        self.wait = None
        
        self.setup_logging()
        
    def setup_logging(self):
        logger = logging.getLogger()
        
        if not any(isinstance(h, logging.FileHandler) for h in logger.handlers):
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            logging.getLogger().addHandler(console_handler)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            filename=self.config.log_file,
            filemode='a'
        )
    
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
                    
    def _validate_file_path(self, file_path: str) -> bool:
        if not file_path or not os.path.exists(file_path):
            logging.error(f"Arquivo não encontrado: {file_path}")    
            return False
        
        return True
    
    def security_check(self) -> bool:
        try:
            for pattern in self.config.SECURITY_WARNING_PATTERNS:
                try:
                    logging.info("Procurando janela de segurança")
                    app = Application(backend="win32").connect(
                        title_re=pattern,
                        timeout=self.config.SECURITY_CHECK_TIMEOUT
                    )
                    dlg = app.window(title_re=pattern)  # Corrigido 'tittle_re'
                    
                    if dlg.exists():
                        logging.info(f"Janela de segurança encontrada: {pattern}")
                        try:
                            dlg.type_keys("{TAB}" * 2 + "{ENTER}", pause=0.1)
                            logging.info("Janela de segurança fechada com sucesso")
                            return True
                        except Exception as e:
                            logging.error(f"Erro ao fechar janela de segurança: {str(e)}")
                            
                except ProcessNotFoundError:
                    logging.debug(f"Janela de segurança não encontrada: {pattern}")
                    continue
                except Exception as e:
                    logging.error(f"Erro ao procurar janela de segurança: {str(e)}")
                    continue
            logging.warning("Nenhuma janela de segurança encontrada")
            return False
        
        except Exception as e:
            logging.error(f"Erro na verificação de segurança: {str(e)}")
            return False
        
    def recognize_3270_terminal(self) -> bool:
        start_time = time.time()
        timeout = self.config.TERMINAL_RECOGNITION_TIMEOUT
        
        while time.time() - start_time < timeout:
            try:
                for pattern in self.config.TERMINAL_PATTERNS:
                    try:
                        logging.info(f"Procurando terminal 3270")
                        terminal_app = Application(backend="win32").connect(
                            title_re=pattern,
                            timeout=5
                        )
                        terminal_dlg = terminal_app.window(title_re=pattern)
                        
                        if terminal_dlg.exists():
                            terminal_dlg.wait('exists', timeout=5)
                            terminal_dlg.wait('visible', timeout=5)
                            terminal_dlg.set_focus()
                            
                            logging.info(f"Terminal 3270 reconhecido: {pattern}")
                            return True
                    except ProcessNotFoundError:
                        logging.debug(f"Terminal 3270 não encontrado: {pattern}")
                        continue
                    except Exception as e:
                        logging.error(f"Erro ao reconhecer terminal 3270: {str(e)}")
                        continue
            
                remaining_time = int(timeout - (time.time() - start_time))
                logging.warning(f"Aguardando terminal... {remaining_time}s restantes")
                time.sleep(2)
                
            except Exception as e:
                logging.error(f"Erro na verificação do terminal 3270: {str(e)}")
                time.sleep(2)
        
        logging.error("Tempo limite excedido para reconhecimento do terminal 3270")
        return False
    
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
    
    def open_3270_emulator(self, file_path: str) -> bool:
        try:
            if not self._validate_file_path(file_path):
                return False
            content = self._read_file_content(file_path)
            if not content:
                logging.error(f"Conteúdo do arquivo {file_path} não pôde ser lido")
                return False
            
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
    
    def check_3270_connection(self) -> bool:
        em = None
        try:
            em = Emulator(visible=True)
            
            if not em.is_connected():
                logging.info("Tentando conectar ao emulador 3270")
                return True
            
            screen_lines = []
            for row in range(1, 25):
                try:
                    line_content = em.string_get(row, 1, 80)
                    screen_lines.append(line_content)
                except Exception:
                    break
            
            screen_content = '\n'.join(screen_lines)
            
            non_empty_lines = [
                line.strip() for line in screen_content.split('\n') 
                if line.strip()
            ]
            
            if len(non_empty_lines) <= 3:
                screen_lower = screen_content.lower()
                disconnected = any(
                    indicator.lower() in screen_lower 
                    for indicator in self.config.DISCONNECTION_INDICATORS
                )
                
                if disconnected:
                    logging.info("Conexão 3270 perdida - indicadores de desconexão encontrados")
                    return True
            
            is_connected = any(
                indicator in screen_content 
                for indicator in self.config.CONNECTION_INDICATORS
            )
            
            if is_connected:
                logging.info("Conexão 3270 ativa")
                return False
            else:
                logging.info("Conexão 3270 inativa")
                return True
                
        except Exception as e:
            logging.error(f"Erro ao verificar conexão 3270: {e}")
            logging.info("Assumindo desconexão devido ao erro")
            return True
        finally:
            if em:
                try:
                    if hasattr(em, 'is_connected') and em.is_connected():
                        logging.info("Desconectando do emulador 3270")
                        em.terminate()
                    else:
                        if hasattr(em, 'close') and em.app:
                            em.app = None
                except Exception:
                    pass
    
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
            
            if not self.security_check():
                logging.error("Falha na verificação de segurança")
                return False
            
            logging.info("Aguardando inicialização do emulador...")
            time.sleep(5)
            
            if not self.recognize_3270_terminal():
                logging.error("Falha ao reconhecer emulador 3270")
                return False
            
            logging.info("Conexão 3270 estabelecida com sucesso")
            time.sleep(3)
            return True
    
    def monitor_3270_connection(self):
        logging.info("Iniciando monitoramento da conexão 3270")
        
        while True:
            try:
                needs_reconnection = self.check_3270_connection()
                
                if needs_reconnection:
                    logging.info("Tentando reconectar...")
                    if self.establish_3270_connection():
                        logging.info("Reconexão bem-sucedida")
                    else:
                        logging.error("Falha na reconexão")
                
                time.sleep(self.config.CONNECTION_CHECK_INTERVAL)
                
            except KeyboardInterrupt:
                logging.info("Monitoramento interrompido pelo usuário")
                break
            except Exception as e:
                logging.error(f"Erro durante monitoramento: {e}")
                time.sleep(self.config.CONNECTION_CHECK_INTERVAL)
    
    def run(self):
        try:
            logging.info("Iniciando automação do mainframe")

            self.driver = self.download.setup_webdriver()
            self.driver.get(self.config.HOST)
            time.sleep(3)
            
            if self.establish_3270_connection():
                self.monitor_3270_connection()
            else:
                logging.error("Falha ao estabelecer conexão inicial")
                
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

def main():
    automation = Mainframe3270Automation()
    automation.run()

if __name__ == "__main__":
    main()