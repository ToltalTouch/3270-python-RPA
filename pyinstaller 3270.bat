@echo off
pyinstaller --onefile --noconfirm --add-data "app;app" main.py
pause