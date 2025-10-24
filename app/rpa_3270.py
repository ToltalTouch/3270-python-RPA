import re
import time
import logging
import pyautogui
from pynput import keyboard
from typing import TYPE_CHECKING

from app.download_terminal import DownloadTerminal
from app.config import AppConfig

class Mainframe3270Automation:
    def __init__(self, config: AppConfig = None, download_terminal: DownloadTerminal = None):
        
        self.config = config or AppConfig()
        self.download_terminal = download_terminal or DownloadTerminal()
        # Não configura logging aqui - será configurado na classe principal
        
    def listar_todas_janelas(self):
        todas_janelas = pyautogui.getAllWindows()
        logging.info("Janelas disponíveis:")
        for janela in todas_janelas:
            logging.info(f"- {janela.title}")

    def encontrar_janela(self, termos_busca: list):
        for termo in termos_busca:
            janelas = pyautogui.getWindowsWithTitle(termo)
            if janelas:
                logging.info(f"Janela encontrada com o termo: '{termo}'")
                return janelas[0]
        return None

    def esperar_janela_desaparecer(self, termos_busca: list, timeout: int = 60, intervalo: int = 2):
        logging.info("Esperando a janela desaparecer...")
        tempo_inicial = time.time()
        
        while time.time() - tempo_inicial < timeout:
            janela = self.encontrar_janela(termos_busca)
            if not janela:
                logging.info("A janela desapareceu.")
                return True
            time.sleep(intervalo)
            
        logging.warning("Timeout atingido. A janela ainda está presente.")
        return False
    
    def esperar_janela_aparecer(self, termos_busca: list, timeout: int = 60, intervalo: int = 2):
        logging.info("Esperando a janela aparecer...")
        tempo_inicial = time.time()
        while time.time() - tempo_inicial < timeout:
            janela = self.encontrar_janela(termos_busca)
            if janela:
                logging.info(f"Janela encontrada")
                return janela
            time.sleep(intervalo)
        logging.warning("Timeout atingido. A janela não apareceu.")
        return None

    def _inserir_token_no_terminal(self, token_message):
        try:
            # Se token_message é uma lista, pegue o primeiro elemento
            if isinstance(token_message, list) and len(token_message) > 0:
                token_text = token_message[0]
            elif isinstance(token_message, str):
                token_text = token_message
            else:
                logging.error("Token inválido - não é string nem lista")
                return
            
            # Extrai apenas os números do token se houver texto adicional
            import re
            numbers_only = re.findall(r'\d+', token_text)
            if numbers_only:
                token_to_insert = numbers_only[0]
                logging.info(f"Inserindo token no terminal: {token_to_insert}")
                pyautogui.write(token_to_insert)
                pyautogui.press('enter')
                logging.info("Token inserido com sucesso no terminal")
            else:
                logging.error(f"Não foi possível extrair números do token: {token_text}")
        except Exception as e:
            logging.error(f"Erro ao inserir token no terminal: {e}")

    def extrair_titulo_janela(self, janela) -> str:
        try:
            titulo_janela_terminal = janela.title
            match = re.search(r'AWV[A-Z0-9]+', titulo_janela_terminal)
            if match:
                codigo_awv = match.group()
                codigo_awp = codigo_awv.replace('AWV', 'AWP')
                return codigo_awp
            else:
                logging.warning("Código AWV não encontrado no título da janela do terminal.")
        except Exception as e:
            logging.error(f"Erro ao extrair título da janela: {e}")

    def reconhecer_janela(self, duracao_total=600, intervalo=25):
        pyautogui.FAILSAFE = False
        logging.info("Iniciando mecanismo anti-timeout com teclas de função.")
        tempo_limite = duracao_total

        # espera a janela de inicialização desaparecer
        sucesso = self.esperar_janela_desaparecer(["INICIANDO", "APLICATIVO", "INICIANDO APLICATIVO"], timeout=60)

        if not sucesso:
            logging.error("A janela de inicialização não fechou a tempo. Abortando.")
            return False

        logging.info("A janela de inicialização foi fechada. Continuando o processo.")

        # verifica se há janela de erro
        janela_erro = self.esperar_janela_desaparecer(["ERRO", "APLICATIVO", "ERRO DE APLICATIVO"])
        if not janela_erro:
            logging.error("Janela de erro detectada. Abortando.")
            return False
        
        janela_painel = self.esperar_janela_aparecer(["PAINEL DE CONTROLE", "PAINEL", "CONTROLE"])
        if janela_painel:
            logging.info("Janela do painel de controle detectada. Selecionando impressora.")
            janela_painel.activate()
            pyautogui.press('tab', presses=3, interval=0.3)
            pyautogui.write('IMPRESSORA 3270')
            pyautogui.press('enter')
        
        # localizar o terminal
        janela_terminal = self.esperar_janela_aparecer(["TERMINAL 3270", "3270 TERMINAL", "IBM 3270"])
        if not janela_terminal:
            logging.info("Janela do terminal não encontrada. Encerrando.")
            return False

        titulo_extraido = self.extrair_titulo_janela(janela_terminal)
        if titulo_extraido:
            logging.info(f"Título extraído do terminal: {titulo_extraido}")
        else:
            logging.warning("Não foi possível extrair o título do terminal.")
            
        try:
            janela_terminal.activate()
        except Exception:
            logging.warning("Não foi possível ativar a janela do terminal, tentando prosseguir.")

        # tenta maximizar de forma resiliente
        try:
            pyautogui.hotkey('alt', 'space')
            time.sleep(0.2)
            pyautogui.press('x')
            logging.info("Janela maximizada.")
        except Exception as e:
            logging.warning(f"Erro ao maximizar a janela: {e}")

        time.sleep(1)
        # Usa o token armazenado durante o processo de login (se houver)
        try:
            has_token, token_message = self.download_terminal.get_stored_token()
            if has_token:
                self._inserir_token_no_terminal(token_message)
            else:
                logging.info("Nenhum token armazenado encontrado, continuando operação normal.")
        except Exception as e:
            logging.error(f"Erro ao recuperar token armazenado: {e}")
            logging.info("Continuando sem inserção de token.")

        # Teclas que geralmente são seguras em terminais 3270
        teclas_seguras = ['f5']
            
        while tempo_limite > 0:
            teclado_ativo = False
            
            def on_press(key):
                nonlocal teclado_ativo
                teclado_ativo = True
                return False  # Parar o listener após a primeira tecla pressionada
                
            listener = keyboard.Listener(on_press=on_press)
            listener.start()
            
            time.sleep(intervalo)
                
            listener.stop()
                
            janela_ativa_antes = pyautogui.getActiveWindow()
                
            if janela_terminal == janela_ativa_antes:
                if teclado_ativo:
                    logging.info("Atividade do teclado detectada. Pulando esta iteração.")
                    tempo_limite -= intervalo
                    continue
                    
            # Alternar entre teclas seguras
            tecla_atual = teclas_seguras[int(tempo_limite/intervalo) % len(teclas_seguras)]
            
            try:
                estava_minimizada = hasattr(janela_terminal, "isMinimized") and janela_terminal.isMinimized
                janela_terminal.activate()
                time.sleep(0.5)
                if estava_minimizada:
                    janela_terminal.maximize()
            except Exception:
                logging.warning("Não foi possível ativar/maximizar a janela do terminal, tentando prosseguir.")
                
            # Usar ATTN ou RESET pode ser melhor que ESC em terminais 3270
            pyautogui.hotkey(tecla_atual)
            logging.info(f"Tecla '{tecla_atual}' pressionada para manter sessão ativa.")
                    
            if janela_ativa_antes:
                janela_ativa_antes.activate()
                
            try:
                if estava_minimizada:
                    janela_terminal.minimize()
                    logging.info("Janela do terminal minimizada novamente.")
            except Exception:
                logging.warning("Não foi possível minimizar a janela do terminal novamente.")
                    
            tempo_limite -= intervalo
                
        return True