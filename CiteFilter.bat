@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" (
    echo CiteFilter is not set up yet. Double-click setup_windows.bat first.
    echo.
    pause
    exit /b 1
)
start "" ".venv\Scripts\pythonw.exe" citefilter_ui.py
