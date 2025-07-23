import os
from dataclasses import dataclass
from typing import List
import logging

@dataclass
class AppConfig:
    HOST: str = r'https://hod.serpro.gov.br/a83016cv/'

    DEFAULT_TIMEOUT: int = 60
    ELEMENT_WAIT_TIMEOUT: int = 260
    SECURITY_CHECK_TIMEOUT: int = 15
    TERMINAL_RECOGNITION_TIMEOUT: int = 40
    CONNECTION_CHECK_INTERVAL: int = 20

    MAX_RETRIES: int = 3

    # Corrigido: extensões comuns para arquivos de terminal 3270
    DOWNLOAD_FILE_EXTENSIONS: List[str] = None

    SECURITY_WARNING_PATTERNS: List[str] = None
    TERMINAL_PATTERNS: List[str] = None
    DISCONNECTION_INDICATORS: List[str] = None
    CONNECTION_INDICATORS: List[str] = None

    def __post_init__(self):
        if self.DOWNLOAD_FILE_EXTENSIONS is None:
            # Extensões mais comuns para arquivos de terminal 3270
            self.DOWNLOAD_FILE_EXTENSIONS = ['.jsp']
            
        if self.SECURITY_WARNING_PATTERNS is None:
            self.SECURITY_WARNING_PATTERNS = [".*Advertência de Segurança.*"]

        if self.TERMINAL_PATTERNS is None:
            self.TERMINAL_PATTERNS = [".*Terminal 3270.*"]

        if self.DISCONNECTION_INDICATORS is None:
            self.DISCONNECTION_INDICATORS = ["MA?",
                                            "Desconectado",
                                            "659",
                                            "/001"]
        
        if self.CONNECTION_INDICATORS is None:
            self.CONNECTION_INDICATORS = ["MENU DE SISTEMA",
                                         "CODIGO",
                                         "USUARIO",
                                         "PF3",
                                         "PF7"]
    
    @property
    def download_dir(self) -> str:
        return f"C:\\Users\\{os.getlogin()}\\Downloads"
    
    @property
    def edge_path(self) -> str:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(current_dir, "edgedriver_win64", "msedgedriver.exe")
    
    @property
    def log_file(self) -> str:
        current_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(current_dir, 'mainframe_automation.log')