from pywinauto.application import Application
from pywinauto import clipboard
from pywinauto.keyboard import send_keys
import time

from config import AppConfig

class RPA3270:
    def __init__(self, window_title):
        self.config = AppConfig()
        self.screen = ''
        self.delay = 0.1
        self.app = Application(backend="win32").connect(title=window_title)
        self.dlg = self.app.top_window()
        self.window = self.app.window(title=window_title)
        
        self.keysCommands = ('ENTER','PF1','PF2','PF3','PF4','PF5','PF6','PF7',
                          'PF8','PF9','PF10','PF11','PF12','PA1','PA2','END',
                          'HOME')
        self.digitalCommands = ('{ENTER}','{F1}','{F2}','{F3}','{F4}','{F5}','{F6}','{F7}',
                                '{F8}','{F9}','{F10}','{F11}','{F12}','{PGUP}','{PGDN}','{END}',
                                '{HOME}')
        
    def select_window(self):
        self.dlg = self.app.top_window()
        time.sleep(1)
        
    def space_bar(self, N):
        n_spaces = N
        argumento = "{VK_SPACE " + str(n_spaces) + "}"
        self.dlg.type_keys(argumento)
        
    def tab(self, N):
        n_tabs = N
        if N < 0:
            self.dlg.type_keys('{VK_SHIFT down}')
            n_tabs = abs(N)
        argumento = "{VK_TAB " + str(n_tabs) + "}"
        self.dlg.type_keys(argumento)
        if N < 0:
            self.dlg.type_keys('{VK_SHIFT up}')
            
    def posicion_cursor(self, tabs):
        self.dlg.type_keys('{HOME}')
        self.tab(tabs)
        
    def digita(self, text):
        time.sleep(self.delay)
        text = str(text)
        text = text.replace(' ', '{SPACE}')
        self.dlg.type_keys(text)
        time.sleep(self.delay)
        
    def _enter(self):
        time.sleep(self.delay)
        self.dlg.type_keys('{ENTER}')
        time.sleep(self.delay)
        
    def command_key(self, key):
        position = self.keysCommands.index(key)
        time.sleep(self.delay)
        self.dlg.type_keys(self.digitalCommands[position])
        time.sleep(self.delay)
        
    def copy_screen(self):
        self.dlg.type_keys('^a')
        time.sleep(self.delay)
        self.dlg.type_keys('^c')
        time.sleep(self.delay)
        self.screen = clipboard.GetData()
        return clipboard.GetData()
     
    def next_screen(self, key):
        self.dlg = self.app.top_window()
        initial_screen = self.copy_screen()
        self.screen = initial_screen
        self.command_key(key)
        
        while self.screen == initial_screen:
            time.sleep(self.delay)
            self.screen = self.copy_screen()
        return self.screen
        
    def get_text(self, screen, L1, C1, L2, C2):
        D1 = (L1 - 1) * 82 + C1 - 1
        D2 = (L2 - 1) * 82 + C2
        return screen[D1:D2]
    
    def save_text(self, screen, L1, C1, L2, C2, text, commandKey):
        screen_found = 0
        while screen_found == 0:
            time.sleep(self.delay)
            self.screen = self.copy_screen()
            if self.get_text(self.screen, L1, C1, L2, C2) == text:
                screen_found =1
            else:
                self.next_screen(commandKey)
                
    def wait_screen_anyware(self, tuple_text, commandKey):
        self.D1 = 0
        self.D2 = 0
        self.L = 0
        self.C1 = 0
        self.C2 =0
        self.found = False
        
        def search_text():
            for text in tuple_text:
                if text in self.screen:
                    self.D1 = self.screen.find(text) + 1
                    self.D2 = self.D1 + len(text) -1
                    self.L = self.D1 // 82 + 1
                    self.C1 = self.D1 % 82 + 1
                    self.C2 = self.C1 + len(text) - 1
                    self.textCoords = (self.L, self.C1, self.L, self.C2, tuple_text.index(text))
                    self.found = True
                    return
                    
        self.screen = self.copy_screen()
        search_text()
        while not self.found:
            self.screen = self.next_screen(commandKey)
            search_text()
        return self.textCoords