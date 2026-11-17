@echo off
pyinstaller --onedir --noconfirm --name "3270-python-RPA" --add-data "app;app" main.py
pause
