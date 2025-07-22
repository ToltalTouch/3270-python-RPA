import getpass
import logging
from typing import Tuple, Optional

class CredentialManager:
    def __init__(self):
        self._username = None
        self._password = None

    def get_credentials(self, username: Optional[str] = None,
                        password: Optional[str] = None,
                        retry_attempts: int = 0) -> Tuple[Optional[str], Optional[str]]:
        
        try:
            username = username or self._username
            password = password or self._password

            if retry_attempts == 0:  # Corrigido: primeira tentativa
                logging.info("Obtendo credenciais do usuário.")
            else:
                logging.info(f"Tentativa {retry_attempts + 1} - Digite novamente")

            if username is None or retry_attempts > 0:
                username = input("Digite o CPF:")
                self._username = username
            
            if password is None or retry_attempts > 0:
                password = getpass.getpass("Digite a senha:")
                self._password = password
            
            return username, password
        
        except Exception as e:
            logging.error(f"Erro ao obter credenciais: {str(e)}")
            return None, None
        
    def clear_credentials(self):
        self._username = None
        self._password = None