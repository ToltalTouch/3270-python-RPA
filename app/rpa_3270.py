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
                pyautogui.press('f5')
                time.sleep(0.5)
                pyautogui.write(token_to_insert)
                pyautogui.press('enter')
                logging.info("Token inserido com sucesso no terminal")
            else:
                logging.error(f"Não foi possível extrair números do token: {token_text}")
        except Exception as e:
            logging.error(f"Erro ao inserir token no terminal: {e}")

        
    def reconhecer_janela(self, duracao_total=300, intervalo=15):
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
        janela_erro = self.encontrar_janela(["ERRO", "APLICATIVO", "ERRO DE APLICATIVO"])
        if janela_erro:
            logging.error("Janela de erro detectada. Encerrando o processo.")
            return False

        # localizar o terminal
        janela_terminal = self.encontrar_janela(["TERMINAL 3270", "3270 TERMINAL", "IBM 3270"])
        if not janela_terminal:
            logging.info("Janela do terminal não encontrada. Encerrando.")
            return False

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

        # Usa o token armazenado durante o processo de login (se houver)
        try:
            has_token, token_message = self.download_terminal.get_stored_token()
            if has_token:
                logging.info(f"Token de autenticação armazenado detectado: {token_message}. Inserindo no terminal.")
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

            # Aguarda o listener terminar ou o timeout do intervalo
            listener.join(timeout=intervalo)
            if listener.is_alive():
                try:
                    listener.stop()
                except Exception:
                    pass

            janela_ativa_antes = pyautogui.getActiveWindow()

            # se terminal está ativo, respeitar atividade do teclado
            if janela_terminal == janela_ativa_antes and teclado_ativo:
                logging.info("Terminal ativo com digitação detectada — pulando ação.")
                tempo_limite -= intervalo
                continue

            # envia tecla de manutenção
            tecla_atual = teclas_seguras[int(tempo_limite / intervalo) % len(teclas_seguras)]

            try:
                janela_terminal.activate()
                time.sleep(0.25)
                pyautogui.press(tecla_atual)
                logging.info(f"Tecla '{tecla_atual}' pressionada para manter sessão ativa.")
            except Exception as e:
                logging.error(f"Erro ao ativar/enviar tecla ao terminal: {e}")

            # tenta restaurar o foco anterior
            try:
                if janela_ativa_antes:
                    janela_ativa_antes.activate()
            except Exception:
                pass

            tempo_limite -= intervalo

        return True