import os
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