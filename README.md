# Automação de Terminal 3270 (IBM Mainframe)

Este projeto demonstra como automatizar interações com sistemas IBM Mainframe através da interface de terminal 3270, usando Python e a biblioteca py3270.

## Sobre o Terminal 3270

O Terminal 3270 é uma interface para interagir com sistemas legados de mainframe IBM:
- Utilizado em instituições públicas e privadas com sistemas COBOL
- Acessado através de emuladores TN3270
- Normalmente exibe menus com sistemas disponíveis como CGRS, ORYX, SGP, SIMCD, etc.

## Pré-requisitos

1. Python 3.6+
2. Biblioteca py3270 (`pip install py3270`)
3. Emulador x3270 ou compatível:
   - Linux: `sudo apt-get install x3270`
   - Windows: Baixe e instale x3270 de [x3270.org](http://x3270.org/)

## Configuração

Edite as variáveis no início do arquivo `3270-python-RPA.py`:
```python
host = 'seu.mainframe.gov.br'
username = 'SEU_USUARIO'
password = 'SUA_SENHA'
sistema = 'SISTEMA_DESEJADO'
```

**Importante**: Para ambientes de produção, utilize variáveis de ambiente ou um sistema de gerenciamento de segredos para credenciais.

## Como Usar

Execute o script:
```
python 3270-python-RPA.py
```

## Funcionalidades Principais

### 1. Leitura da Tela (`string_get`)

Uma das funções mais importantes para automação inteligente é a leitura do conteúdo da tela:

```python
# Lê o texto na linha 24, coluna 1, com comprimento 40
texto = emulator.string_get(24, 1, 40)
```

Coordenadas importantes em telas 3270:
- Linha 1: Geralmente contém o título da tela
- Linha 24: Geralmente contém mensagens de status ou erro
- Linhas 2-23: Conteúdo principal e campos de entrada

### 2. Navegação

Teclas de função PF são importantes para navegação em sistemas mainframe:

```python
# Tecla PF3 (normalmente para voltar/sair)
emulator.exec_command(b"PF(3)")

# Tecla PF1 (normalmente para ajuda)
emulator.exec_command(b"PF(1)")
```

### 3. Automação Avançada

Para automação mais avançada:
- Use `verify_screen_content()` para validar o estado da tela
- Implemente loops de espera para telas com carregamento lento
- Crie funções específicas para cada tipo de operação no seu sistema

## Dicas para Automação de Mainframe

- **Mapeie a tela**: Antes de automatizar, documente as posições dos campos
- **Trate erros**: Mainframes frequentemente possuem mensagens de erro específicas
- **Use timeouts apropriados**: Sistemas mainframe podem ter latência variável
- **Faça logging detalhado**: Ajuda na depuração de problemas de automação

## Exemplo de Uso da Função `verify_screen_content`

```python
# Verifica se login foi bem-sucedido
texto, sucesso = verify_screen_content(
    emulator, 
    row=24,                        # Linha de status
    col=1,                         # Primeira coluna
    length=40,                     # Comprimento a ler
    expected_text="BEM-VINDO",     # Texto de sucesso
    error_texts=["SENHA INVÁLIDA", "USUÁRIO BLOQUEADO"]  # Erros possíveis
)
```

## Recursos Adicionais

- [Documentação py3270](https://pypi.org/project/py3270/)
- [Guia de terminais 3270](https://www.ibm.com/support/knowledgecenter/zosbasics/com.ibm.zos.zconcepts/zconc_3270.htm)
