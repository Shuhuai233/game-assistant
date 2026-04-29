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

:: Build (use python -m to avoid PATH issues)
echo.
echo [2/3] Building exe (this may take a few minutes)...
python -m PyInstaller game_assistant.spec --clean

:: Copy config
echo.
echo [3/3] Copying config file...
if not exist "dist\config.yaml" (
    copy config.yaml dist\config.yaml
)

echo.
if exist "dist\GameAssistant.exe" (
    echo ==========================================
    echo   Build successful!
    echo   Output: dist\GameAssistant.exe
    echo ==========================================
) else (
    echo ==========================================
    echo   Build FAILED. Check errors above.
    echo ==========================================
)
echo.
pause
