@echo off
pyinstaller --onedir ^
--add-data "C:\python\3270-python-RPA\edgedriver_win64\*;edgedriver_win64" ^
--add-data "C:\python\3270-python-RPA\__pycache__\*;__pycache__" ^
--add-data "C:\python\3270-python-RPA\config.py;." ^
--add-data "C:\python\3270-python-RPA\credential_manager.py;." ^
--add-data "C:\python\3270-python-RPA\download_terminal.py;." ^
3270-python-RPA.py
pause