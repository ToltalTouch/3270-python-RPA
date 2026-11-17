# Automação de Terminal 3270 (SERPRO Mainframe) - RPA

Este projeto é uma solução de **RPA (Robotic Process Automation)** desenvolvida em Python para automatizar o processo de autenticação, inicialização, configuração e manutenção de sessão ativa (*keep-alive / anti-timeout*) no **Terminal 3270 (Host On Demand - HOD)** do **SERPRO**.

---

## 📌 Visão Geral do Funcionamento

O fluxo de execução do programa contempla as seguintes etapas automáticas:

1. **Solicitação de Credenciais**:
   - Solicita o CPF e a senha do usuário de forma interativa e segura no terminal (com senha oculta via `getpass`).
2. **Autenticação Web (Selenium + Edge Driver)**:
   - Acessa a página de autenticação do SERPRO HOD em modo *headless*.
   - Preenche as credenciais, submete o formulário e captura eventuais tokens gerados na tela.
3. **Download e Lançamento do Terminal**:
   - Realiza o download do arquivo de inicialização da sessão (`.jsp`).
   - Lança o arquivo no ambiente do sistema operacional (`os.startfile`) para disparar o emulador 3270.
4. **Tratamento de Janelas e Segurança (PyWinAuto)**:
   - Detecta e fecha automaticamente a janela de aviso de segurança do Java/Windows.
   - Trata telas intermediárias (como seleção de impressora no painel de controle, quando aplicável).
5. **Reconhecimento do Terminal e Inserção de Token (PyAutoGUI)**:
   - Localiza a janela ativa do Terminal 3270 e a maximiza.
   - Extrai o identificador da sessão (`AWV`/`AWP`) a partir do título da janela.
   - Insere o token de autenticação capturado no terminal e confirma com Enter.
6. **Mecanismo Anti-Timeout (Keep-Alive com Pynput)**:
   - Mantém a sessão do terminal ativa enviando teclas seguras (`F5`) em intervalos regulares (padrão de 25 segundos, por 10 minutos).
   - **Detecção de atividade**: se o usuário estiver digitando no terminal, o programa pausa o envio para não interferir na digitação manual.
7. **Limpeza e Logs**:
   - Remove arquivos temporários de download com segurança.
   - Registra todo o histórico detalhado da execução no console e no arquivo `mainframe_automation.log`.

---

## 📋 Pré-requisitos de Sistema

- **Sistema Operacional**: Windows 10 ou 11 (64-bit).
- **Python**: Versão 3.8 ou superior.
- **Navegador**: Microsoft Edge instalado.
- **Edge WebDriver**: O executável `msedgedriver.exe` já está incluído na pasta `app/edgedriver_win64/`. Caso a versão do seu Microsoft Edge seja atualizada, certifique-se de baixar o driver correspondente no portal oficial da Microsoft e substituir o binário existente.
- **Ambiente Java / HOD**: Configuração do sistema pronta para executar arquivos `.jsp` associados ao Host On Demand do SERPRO.

---

## 🚀 Instalação e Configuração

### 1. Clonar ou Acessar o Repositório

Abra o PowerShell ou Prompt de Comando na pasta do projeto:

```powershell
cd c:\PYTHON\3270-python-RPA
```

### 2. Criar e Ativar o Ambiente Virtual (Recomendado)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

*(No Prompt de Comando comum: `venv\Scripts\activate.bat`)*

### 3. Instalar as Dependências

Instale os pacotes Python necessários através do arquivo `requirements.txt`:

```powershell
pip install -r requirements.txt
```

---

## ▶️ Como Executar o Programa

### Execução via Python (Desenvolvimento)

Com o ambiente ativado, execute o ponto de entrada principal:

```powershell
python main.py
```

Durante a execução:
1. Digite o **CPF** quando solicitado.
2. Digite a **Senha** (os caracteres não serão exibidos por segurança).
3. O robô assumirá o controle em segundo plano, realizando o download, abrindo o terminal e mantendo a sessão ativa.

---

## ⚙️ Configurações Customizáveis (`app/config.py`)

No arquivo [app/config.py](file:///c:/PYTHON/3270-python-RPA/app/config.py), você pode ajustar parâmetros como:

- `HOST`: URL do Host On Demand SERPRO (`https://hod.serpro.gov.br/a83016cv/`).
- `DEFAULT_TIMEOUT` / `ELEMENT_WAIT_TIMEOUT`: Prazos de espera para elementos web e downloads.
- `SECURITY_CHECK_TIMEOUT`: Tempo limite para interceptar avisos de segurança.
- `MAX_RETRIES`: Número máximo de tentativas de login e download (padrão: 3).
- `duracao_total` e `intervalo` (em [app/rpa_3270.py](file:///c:/PYTHON/3270-python-RPA/app/rpa_3270.py)): Tempo total do anti-timeout (padrão: 600 segundos) e intervalo de pulso (padrão: 25 segundos).

---

## 📦 Gerando o Executável e o Instalador

### 1. Criar Executável com PyInstaller

Você pode gerar um arquivo `.exe` portátil executando o arquivo em lote:

```powershell
.\pyinstaller 3270.bat
```

Ou diretamente via comando:

```powershell
pyinstaller --onefile --noconfirm --add-data "app;app" main.py
```

O binário final será gerado no diretório `dist/`.

### 2. Criar Instalador Windows (Inno Setup)

Para distribuir o programa como instalador do Windows:
1. Abra o arquivo [inno 3270.iss](file:///c:/PYTHON/3270-python-RPA/inno 3270.iss) no [Inno Setup Compiler](https://jrsoftware.org/isinfo.php).
2. Clique em **Compile** (ou pressione `Ctrl + F9`).
3. O instalador `Terminal3270Setup.exe` será gerado na pasta `Output/`.

---

## 📂 Estrutura de Arquivos

```
3270-python-RPA/
│
├── app/
│   ├── edgedriver_win64/
│   │   └── msedgedriver.exe      # Driver do Edge para automação web
│   ├── __init__.py               # Inicializador do pacote Python
│   ├── config.py                 # Configurações gerais e logging
│   ├── credential_manager.py     # Coleta segura de credenciais (CPF/Senha)
│   ├── download_terminal.py      # Automação Selenium para login e download do .jsp
│   ├── open_3270.py              # Orquestrador do ciclo de vida e lançamento
│   └── rpa_3270.py               # RPA desktop, detecção de janelas e anti-timeout
│
├── main.py                       # Ponto de entrada da aplicação
├── requirements.txt              # Dependências do projeto
├── pyinstaller 3270.bat          # Script de empacotamento com PyInstaller
├── inno 3270.iss                 # Script de criação de instalador Windows
└── README.md                     # Documentação do projeto
```

---

## 🔍 Logs e Diagnóstico

- O log de execução é exibido em tempo real no console e salvo simultaneamente em [mainframe_automation.log](file:///c:/PYTHON/3270-python-RPA/mainframe_automation.log).
- Caso o terminal não seja localizado ou o login falhe, consulte o log para verificar em qual etapa ocorreu a interrupção (ex: timeout de elemento, divergência de versão do WebDriver ou título de janela não reconhecido).

---

## 🔒 Segurança e LGPD

- As credenciais de acesso (CPF e senha) são solicitadas em tempo de execução e **não** são salvas em arquivos locais ou em disco.
- Todos os arquivos temporários baixados durante o processo são excluídos automaticamente após o uso.
