import os
import logging
from dataclasses import dataclass
from typing import List

@dataclass
class AppConfig:
    # Link para download do token de acesso ao SERPRO
    HOST: str = r'https://hod.serpro.gov.br/a83016cv/'

    # tamanho padrao da tela do terminal 3270
    LINE_WIDTH: int = 82

    # Tempo de espera padrão para ações
    DEFAULT_TIMEOUT: int = 60
    ELEMENT_WAIT_TIMEOUT: int = 260
    SECURITY_CHECK_TIMEOUT: int = 15
    TERMINAL_RECOGNITION_TIMEOUT: int = 40
    CONNECTION_CHECK_INTERVAL: int = 20

    # Tentativas máximas para reconexão
    MAX_RETRIES: int = 3

    # extensões comuns para arquivos de terminal 3270
    DOWNLOAD_FILE_EXTENSIONS: List[str] = None
    SECURITY_WARNING_PATTERNS: List[str] = None
    TERMINAL_PATTERNS: List[str] = None
    DISCONNECTION_INDICATORS: List[str] = None
    CONNECTION_INDICATORS: List[str] = None

    # patterns padrões de exteção e janelas
    def __post_init__(self):
        if self.DOWNLOAD_FILE_EXTENSIONS is None:
            self.DOWNLOAD_FILE_EXTENSIONS = ['.jsp']
            
        if self.SECURITY_WARNING_PATTERNS is None:
            self.SECURITY_WARNING_PATTERNS = [".*Advertência de Segurança.*"]

        if self.TERMINAL_PATTERNS is None:
            self.TERMINAL_PATTERNS = [".*Terminal 3270.*"]

    # caminho padrao para diretorio de download
    # utilizando o nome do usuario logado
    @property
    def download_dir(self) -> str:
        return f"C:\\Users\\{os.getlogin()}\\Downloads"
    
    # caminho para o driver do edge
    @property
    def edge_path(self) -> str:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(current_dir, "edgedriver_win64", "msedgedriver.exe")
    
    # caminho para arquivo log
    @property
    def log_file(self) -> str:
        current_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(current_dir, 'mainframe_automation.log')

def setup_logging(log_file: str = None) -> logging.Logger:
    """
    Configura o sistema de logging de forma centralizada para evitar duplicações.
    
    Args:
        log_file: Caminho para o arquivo de log. Se None, usa o padrão do AppConfig.
    
    Returns:
        Logger configurado
    """
    # Obtém o logger raiz
    logger = logging.getLogger()
    
    # Se já está configurado, não configura novamente
    if logger.handlers:
        return logger
    
    # Define o nível do logger
    logger.setLevel(logging.INFO)
    
    # Configura o formato das mensagens
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # Handler para arquivo
    if log_file is None:
        config = AppConfig()
        log_file = config.log_file
    
    try:
        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Erro ao criar file handler: {e}")
    
    # Handler para console
    try:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    except Exception as e:
        print(f"Erro ao criar console handler: {e}")
    
    # Evita propagação para handlers pais
    logger.propagate = False
    
    logging.info("Sistema de logging configurado com sucesso")
    return logger