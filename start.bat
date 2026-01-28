@echo off
chcp 65001 >nul
title SKYNET - Personal AI Assistant

echo.
echo ========================================
echo    SKYNET - Personal AI Assistant
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

REM Create data folder if not exists
if not exist "data" mkdir data

REM Check if hardware config exists
if exist "data\hardware_config.json" (
    echo [Skynet] Configuracao de hardware encontrada.
    goto :start_app
)

:select_hardware
echo.
echo ================================================================
echo                 SELECAO DE HARDWARE PARA IA
echo ================================================================
echo.
echo   [1] CPU - Funciona em qualquer PC (mais lento)
echo.
echo   [2] GPU NVIDIA - Para placas GeForce/RTX (CUDA)
echo.
echo   [3] GPU AMD - Para placas Radeon/RX (DirectML)
echo       Ex: RX 6650 XT, RX 7900, etc.
echo.
echo ================================================================
echo.

set /p hardware_choice="Escolha [1/2/3]: "

if "%hardware_choice%"=="1" (
    echo.
    echo [Skynet] Configurando para CPU...
    call :setup_cpu
    goto :start_app
)

if "%hardware_choice%"=="2" (
    echo.
    echo [Skynet] Configurando para NVIDIA GPU...
    call :setup_nvidia
    goto :start_app
)

if "%hardware_choice%"=="3" (
    echo.
    echo [Skynet] Configurando para AMD GPU...
    call :setup_amd
    goto :start_app
)

echo [ERRO] Opcao invalida. Escolha 1, 2 ou 3.
goto :select_hardware

:setup_cpu
echo [Setup] Instalando dependencias para CPU...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu -q 2>nul
echo {"hardware": "cpu"} > data\hardware_config.json
echo [Setup] CPU configurada!
goto :eof

:setup_nvidia
echo [Setup] Verificando NVIDIA GPU...
nvidia-smi >nul 2>&1
if errorlevel 1 (
    echo [AVISO] nvidia-smi nao encontrado.
    echo [AVISO] Certifique-se de que os drivers NVIDIA estao instalados.
)
echo [Setup] Instalando PyTorch com CUDA...
echo [Setup] Isso pode demorar alguns minutos...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 -q 2>nul
echo {"hardware": "nvidia"} > data\hardware_config.json
echo [Setup] NVIDIA CUDA configurado!
goto :eof

:setup_amd
echo [Setup] Configurando AMD GPU com DirectML...
echo [Setup] Instalando dependencias para AMD...
echo [Setup] Isso pode demorar alguns minutos...
pip install torch-directml -q 2>nul
pip install onnxruntime-directml -q 2>nul
pip install optimum[onnxruntime] -q 2>nul
echo {"hardware": "amd"} > data\hardware_config.json
echo [Setup] AMD DirectML configurado!
goto :eof

:start_app
echo.
echo [Skynet] Iniciando aplicacao...
echo.

REM Clear previous log file to avoid accumulation
if exist "data\skynet.log" del "data\skynet.log"

REM Set environment variables to fix pywebview errors
set PYWEBVIEW_GUI=edgechromium
set PYTHONIOENCODING=utf-8
set PYWEBVIEW_NO_UIA=1

REM Run application (errors will be logged to data\skynet.log)
python desktop_app.py 2>> data\skynet.log

if errorlevel 1 (
    echo.
    echo [ERRO] Falha ao iniciar a aplicacao.
    echo Verifique o arquivo data\skynet.log para mais detalhes.
    echo Verifique se todas as dependencias estao instaladas.
    pause
)
