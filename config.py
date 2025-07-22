import os
from datacalasses import dataclass
from typing import List

@dataclass
class AppConfig:
    HOST: str = r'https://hod.serpro.gov.br/a83016cv/'

    DEFAULT_TIMEOUT: int = 60
    ELEMENT_WAIT_TIMEOUT: int = 260
    SECURITY_CHECK_TIMEOUT: int = 15
    TERMINAL_REGONITION_TIMEOUT: int = 40
    CONNECTION_CHECK_INTERVAL: int = 20

    MAX_RETRIE: int = 3

    DOWNLOAD_FILE_EXTENSION: str = '.jsp'

    SECURITY_WARNING_PATTERNS: List[str] = None
    TERMINAL_PATTERNS: List[str] = None
    DISCONNECTION_INDICATOR: List[str] = None
    CONNECTION_INDICATOR: List[str] = None

    def __post_init__(self):
        if self.SECURITY_WARNING_PATTERNS is None:
            self.SECURITY_WARNING_PATTERNS = [".*Advertência de Segurança.*"]

        if self.TERMINAL_PATTERNS is None:
            self.TERMINAL_PATTERNS = [".*Terminal 3270.*"]

        if self.DISCONNECTION_INDICATOR is None:
            self.DISCONNECTION_INDICATOR = ["MA?",
                                            "Desconectado",
                                            "659",
                                            "/001"]
        
        if self.CONNECTION_INDICATOR is None:
            self.CONNECTION_INDICATOR = ["MENU DE SISTEMA",
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
        return 'mainframe_automation.log'