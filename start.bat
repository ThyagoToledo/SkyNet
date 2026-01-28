@echo off
echo Starting Skynet...
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat 2>nul

REM Check if venv exists
if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found.
    echo Please run install.bat first.
    pause
    exit /b 1
)

REM Start the assistant
python main.py

pause
