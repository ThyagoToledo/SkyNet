@echo off
echo ========================================
echo    SKYNET - Desktop Application
echo ========================================
echo.

cd /d "%~dp0"

REM Check for venv first, then .venv
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else (
    echo [ERRO] Ambiente virtual nao encontrado!
    echo Execute o install.bat primeiro.
    pause
    exit /b 1
)

echo [Skynet] Iniciando aplicacao desktop...
echo.

python desktop_app.py

if errorlevel 1 (
    echo.
    echo [ERRO] Falha ao iniciar a aplicacao.
    echo Verifique se todas as dependencias estao instaladas.
    pause
)
