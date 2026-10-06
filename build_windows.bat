@echo off
setlocal
cd /d "%~dp0"
set "PY="
where py >nul 2>nul
if not errorlevel 1 set "PY=py -3"
if not defined PY (
    where python >nul 2>nul
    if not errorlevel 1 set "PY=python"
)
if not defined PY goto nopython
%PY% windows\build_windows.py %*
goto end

:nopython
echo Python was not found on this PC.
echo.
echo 1. Download Python 3.12 or 3.13 from https://www.python.org/downloads/windows/
echo 2. In its installer, tick "Add python.exe to PATH", then Install.
echo 3. Double-click this file again.

:end
echo.
pause
