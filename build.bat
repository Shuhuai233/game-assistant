@echo off
echo ==========================================
echo   Building Game Assistant .exe
echo ==========================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Install Python 3.9+ first.
    pause
    exit /b 1
)

:: Install dependencies
echo [1/3] Installing dependencies...
pip install -r requirements.txt
pip install pyinstaller

:: Build
echo.
echo [2/3] Building exe (this may take a few minutes)...
pyinstaller game_assistant.spec --clean

:: Copy config
echo.
echo [3/3] Copying config file...
if not exist "dist\config.yaml" (
    copy config.yaml dist\config.yaml
)

echo.
echo ==========================================
echo   Build complete!
echo   Output: dist\GameAssistant.exe
echo ==========================================
echo.
echo Users need to put config.yaml next to GameAssistant.exe
echo or run the app and configure via Settings dialog.
echo.
pause
