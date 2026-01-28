@echo off
echo ========================================
echo    SKYNET - Desktop Application
echo ========================================
echo.

cd /d "%~dp0"

if not exist ".venv\Scripts\activate.bat" (
    if not exist "venv\Scripts\activate.bat" (
        echo [ERRO] Ambiente virtual nao encontrado!
        echo Execute o install.bat primeiro.
        pause
        exit /b 1
    )
    call venv\Scripts\activate.bat
) else (
    call .venv\Scripts\activate.bat
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
