@echo off
title VidCover Tools - Launcher
color 0A

echo.
echo  ====================================
echo   VidCover Tools - Starting...
echo  ====================================
echo.

:: Check if Flask is installed
pip show flask >nul 2>&1
if %errorlevel% neq 0 (
    echo  [*] Installing Flask...
    pip install flask
    echo.
)

:: Run the app
echo  [*] Starting VidCover Tools...
echo.
python "%~dp0app.py"

pause
