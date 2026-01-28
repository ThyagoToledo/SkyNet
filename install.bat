@echo off
echo ============================================
echo    SKYNET - Personal AI Assistant Setup
echo ============================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.10+
    pause
    exit /b 1
)

echo [1/5] Checking virtual environment...
if exist venv\ (
    echo [INFO] Virtual environment already exists. Skipping creation.
) else (
    echo [INFO] Creating new virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
)

echo [2/5] Activating virtual environment...
call venv\Scripts\activate.bat

echo [3/5] Upgrading pip...
python -m pip install --upgrade pip

echo [4/5] Installing dependencies...
pip install -r requirements.txt

REM Try to install PyAudio
echo [5/5] Installing audio dependencies...
pip install pipwin 2>nul
pipwin install pyaudio 2>nul

echo.
echo ============================================
echo    Installation Complete!
echo ============================================
echo.
echo Next steps:
echo 1. Install Ollama from: https://ollama.com/download
echo 2. Run: ollama pull llama3.2
echo 3. Run: start_desktop.bat (or start.bat for web mode)
echo.
echo The AI runs 100%% locally - no API keys needed!
echo.
pause
