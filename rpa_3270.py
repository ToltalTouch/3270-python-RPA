import os
import logging

from class_3270 import RPA3270 
from config import AppConfig

class Mainframe3270Automation:
    def __init__(self, config: AppConfig = None):
        self.config = config or AppConfig()
        self.rpa3270 = RPA3270(self.config.TERMINAL_PATTERNS)
        
        self.setup_logging()
        
    # configuração do log
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
        
    def run(self):
        try:
            cabecalho = '"Restricao' + '"'+'\t'+'"' + 'Titulo' + '"'+'\t'+'"' + 'Grupo' + '"'+'\t'+'"' + 'Descricao"' + '\n'
            saida.write(cabecalho)