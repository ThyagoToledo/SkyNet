"""
Skynet Desktop Application
Desktop wrapper using PyWebView with audio device management
"""

import asyncio
import os
import sys
import json
import threading
import logging
import warnings
from pathlib import Path
from datetime import datetime

# =========================================
# CONFIGURAÇÃO DE LOGGING PARA ARQUIVO
# =========================================
LOG_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, 'skynet.log')  # Log inside data folder

# Configure logging with error handling for file access
log_handlers = [logging.StreamHandler(sys.stdout)]

# Try to add file handler, but don't fail if file is locked
try:
    file_handler = logging.FileHandler(LOG_FILE, mode='a', encoding='utf-8')
    log_handlers.append(file_handler)
except PermissionError:
    # File is locked by another process, use only console
    print(f"[AVISO] Não foi possível abrir {LOG_FILE} para escrita. Logs serão exibidos apenas no console.")
except Exception as e:
    print(f"[AVISO] Erro ao configurar log: {e}")
# =========================================
# Custom Log Filter
# =========================================
class AccessFilter(logging.Filter):
    def filter(self, record):
        msg = record.getMessage()
        if 'AccessibilityObject' in msg or 'recursion' in msg.lower():
            return False
        return True

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=log_handlers
)

# Apply filter to specific loggers
webview_logger = logging.getLogger('pywebview')
webview_logger.addFilter(AccessFilter())
webview_logger.setLevel(logging.ERROR)

# Also apply filter to root logger just in case
logging.getLogger().addFilter(AccessFilter())

# Log session start
logger = logging.getLogger('SkyNet')
logger.info("=" * 60)
logger.info(f"SkyNet Session Started: {datetime.now().isoformat()}")
logger.info("=" * 60)

# Suppress pywebview RecursionError
original_excepthook = sys.excepthook
def custom_excepthook(exc_type, exc_value, exc_tb):
    if exc_type == RecursionError:
        return
    exc_str = str(exc_value)
    if 'AccessibilityObject' in exc_str or 'CoreWebView2' in exc_str:
        return
    original_excepthook(exc_type, exc_value, exc_tb)
    
sys.excepthook = custom_excepthook

# =========================================
# Stderr Filter for pywebview noise
# =========================================
class FilteredStderr:
    """Wrapper para sys.stderr que filtra mensagens do pywebview"""
    BLOCKED_PATTERNS = [
        '[pywebview]',
        'CoreWebView2',
        'ICoreWebView2',
        '__abstractmethods__',
        'E_NOINTERFACE',
        'UI thread'
    ]
    
    def __init__(self, original):
        self.original = original
    
    def write(self, msg):
        if any(pattern in msg for pattern in self.BLOCKED_PATTERNS):
            return  # Ignora mensagem
        self.original.write(msg)
    
    def flush(self):
        self.original.flush()
    
    def __getattr__(self, name):
        return getattr(self.original, name)

# Apply filtered stderr
sys.stderr = FilteredStderr(sys.stderr)
    
sys.excepthook = custom_excepthook

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Fix pywebview accessibility recursion errors BEFORE importing
os.environ['PYWEBVIEW_GUI'] = 'edgechromium'
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Disable Windows UI Automation to prevent recursion errors
os.environ['PYWEBVIEW_NO_UIA'] = '1'

# Increase recursion limit significantly to prevent pywebview accessibility errors
sys.setrecursionlimit(10000)

# Custom exception hook to log errors to file
def exception_hook(exc_type, exc_value, exc_traceback):
    """Log uncaught exceptions to file"""
    if issubclass(exc_type, RecursionError):
        # Silently ignore recursion errors from pywebview accessibility
        logger.debug(f"Recursion error suppressed: {exc_value}")
        return
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = exception_hook

# Suppress pywebview recursion errors globally
import ctypes
try:
    # Disable Windows UI Automation accessibility hooks that cause recursion
    ctypes.windll.ole32.CoInitialize(None)
except:
    pass

try:
    import webview
    # Patch webview to ignore accessibility errors
    original_start = webview.start
    def patched_start(*args, **kwargs):
        try:
            return original_start(*args, **kwargs)
        except RecursionError as e:
            logger.debug(f"Suppressed pywebview recursion error: {e}")
    webview.start = patched_start
except ImportError:
    logger.warning("PyWebView não encontrado. Instalando...")
    os.system(f"{sys.executable} -m pip install pywebview")
    import webview

try:
    import sounddevice as sd
except ImportError:
    logger.warning("SoundDevice não encontrado. Instalando...")
    os.system(f"{sys.executable} -m pip install sounddevice")
    import sounddevice as sd

from dotenv import load_dotenv

load_dotenv()


class AudioDeviceManager:
    """Gerencia dispositivos de áudio do sistema"""
    
    def __init__(self):
        self.selected_input = None
        self.selected_output = None
        self.volume = 100
        self.muted = False
        # Use string path instead of Path object to avoid pywebview serialization issues
        config_dir = os.path.join(os.path.dirname(__file__), "data")
        os.makedirs(config_dir, exist_ok=True)
        self.config_file = os.path.join(config_dir, "audio_config.json")
        self.audio_settings_file = os.path.join(config_dir, "audio_settings.json")
        self.load_config()
        self.load_audio_settings()
    
    def get_input_devices(self):
        """Retorna lista de dispositivos de entrada (microfones)"""
        devices = []
        try:
            device_list = sd.query_devices()
            for i, device in enumerate(device_list):
                if device['max_input_channels'] > 0:
                    devices.append({
                        'id': str(i),
                        'name': device['name'],
                        'channels': device['max_input_channels']
                    })
        except Exception as e:
            logger.error(f"Erro ao listar dispositivos de entrada: {e}")
        return devices
    
    def get_output_devices(self):
        """Retorna lista de dispositivos de saída (alto-falantes)"""
        devices = []
        try:
            device_list = sd.query_devices()
            for i, device in enumerate(device_list):
                if device['max_output_channels'] > 0:
                    devices.append({
                        'id': str(i),
                        'name': device['name'],
                        'channels': device['max_output_channels']
                    })
        except Exception as e:
            logger.error(f"Erro ao listar dispositivos de saída: {e}")
        return devices
    
    def set_devices(self, input_id, output_id):
        """Define os dispositivos de áudio selecionados"""
        self.selected_input = input_id
        self.selected_output = output_id
        self.save_config()
        
        # Aplicar configuração ao SoundDevice
        try:
            if input_id:
                sd.default.device[0] = int(input_id)
            if output_id:
                sd.default.device[1] = int(output_id)
            logger.info(f"Dispositivos configurados: entrada={input_id}, saída={output_id}")
        except Exception as e:
            logger.error(f"Erro ao configurar dispositivos: {e}")
    
    def load_config(self):
        """Carrega configuração salva"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.selected_input = config.get('input')
                    self.selected_output = config.get('output')
                    
                    # Aplicar configuração
                    if self.selected_input or self.selected_output:
                        self.set_devices(self.selected_input, self.selected_output)
        except Exception as e:
            logger.error(f"Erro ao carregar configuração de áudio: {e}")
    
    def save_config(self):
        """Salva configuração"""
        try:
            # Directory is already created in __init__
            with open(self.config_file, 'w') as f:
                json.dump({
                    'input': self.selected_input,
                    'output': self.selected_output
                }, f, indent=2)
            logger.info(f"Configuração de áudio salva em: {self.config_file}")
        except Exception as e:
            logger.error(f"Erro ao salvar configuração de áudio: {e}")
    
    def load_audio_settings(self):
        """Carrega configurações de áudio (volume, mudo, etc)"""
        try:
            if os.path.exists(self.audio_settings_file):
                with open(self.audio_settings_file, 'r') as f:
                    settings = json.load(f)
                    self.volume = settings.get('volume', 100)
                    self.muted = settings.get('muted', False)
                    logger.info(f"Configurações de áudio carregadas: volume={self.volume}, muted={self.muted}")
        except Exception as e:
            logger.error(f"Erro ao carregar configurações de áudio: {e}")
    
    def save_audio_settings(self, volume=None, muted=None):
        """Salva configurações de áudio"""
        try:
            if volume is not None:
                self.volume = volume
            if muted is not None:
                self.muted = muted
            
            with open(self.audio_settings_file, 'w') as f:
                json.dump({
                    'volume': self.volume,
                    'muted': self.muted,
                    'updated_at': datetime.now().isoformat()
                }, f, indent=2)
            logger.info(f"Configurações de áudio salvas: volume={self.volume}, muted={self.muted}")
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar configurações de áudio: {e}")
            return False
    
    def get_audio_settings(self):
        """Retorna as configurações de áudio atuais"""
        return {
            'volume': self.volume,
            'muted': self.muted,
            'input': self.selected_input,
            'output': self.selected_output
        }


class SkynetAPI:
    """API exposta para o JavaScript no WebView"""
    
    def __init__(self):
        self.audio_manager = AudioDeviceManager()
        self.server_task = None
        self.assistant = None
        self.window = None  # Referência para a janela do webview
        self.is_transparent = False
    
    def set_window(self, window):
        """Define a referência para a janela do webview"""
        self.window = window
    
    def get_audio_devices(self):
        """Retorna todos os dispositivos de áudio disponíveis"""
        return {
            'input': self.audio_manager.get_input_devices(),
            'output': self.audio_manager.get_output_devices()
        }
    
    def set_audio_devices(self, input_id, output_id):
        """Define os dispositivos de áudio selecionados"""
        self.audio_manager.set_devices(input_id, output_id)
        return {'success': True}
    
    def get_current_devices(self):
        """Retorna os dispositivos atualmente selecionados"""
        return {
            'input': self.audio_manager.selected_input,
            'output': self.audio_manager.selected_output
        }
    
    def save_audio_settings(self, volume=None, muted=None):
        """Salva configurações de áudio (volume, mudo, etc)"""
        success = self.audio_manager.save_audio_settings(volume, muted)
        return {'success': success}
    
    def get_audio_settings(self):
        """Retorna as configurações de áudio atuais"""
        return self.audio_manager.get_audio_settings()
    
    def set_transparent_mode(self, enabled):
        """Ativa ou desativa o modo transparente da janela"""
        self.is_transparent = enabled
        logger.info(f"[Desktop] Modo transparente: {'ativado' if enabled else 'desativado'}")
        
        if self.window:
            try:
                if enabled:
                    # Enable transparent mode in JS and set window background
                    self.window.evaluate_js("""
                        document.body.classList.add('transparent-mode');
                        document.body.style.background = 'transparent';
                        document.documentElement.style.background = 'transparent';
                        if (window.skynetApp && window.skynetApp.particleSystem) {
                            window.skynetApp.particleSystem.setTransparent(true);
                        }
                    """)
                else:
                    self.window.evaluate_js("""
                        document.body.classList.remove('transparent-mode');
                        document.body.style.background = '#000000';
                        document.documentElement.style.background = '#000000';
                        if (window.skynetApp && window.skynetApp.particleSystem) {
                            window.skynetApp.particleSystem.setTransparent(false);
                        }
                    """)
            except Exception as e:
                logger.error(f"[Desktop] Erro ao mudar transparência: {e}")
        
        return {'success': True, 'transparent': enabled}


def print_banner():
    banner = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║   ███████╗██╗  ██╗██╗   ██╗███╗   ██╗███████╗████████╗        ║
    ║   ██╔════╝██║ ██╔╝╚██╗ ██╔╝████╗  ██║██╔════╝╚══██╔══╝        ║
    ║   ███████╗█████╔╝  ╚████╔╝ ██╔██╗ ██║█████╗     ██║           ║
    ║   ╚════██║██╔═██╗   ╚██╔╝  ██║╚██╗██║██╔══╝     ██║           ║
    ║   ███████║██║  ██╗   ██║   ██║ ╚████║███████╗   ██║           ║
    ║   ╚══════╝╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═══╝╚══════╝   ╚═╝           ║
    ║                                                               ║
    ║              Personal AI Assistant v1.0                       ║
    ║                  Desktop Edition - Local AI                   ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    print(banner)
    logger.info("SkyNet Desktop Edition started")


def select_hardware():
    """Show hardware selection menu"""
    from src.core.hardware_selector import HardwareSelector
    selector = HardwareSelector()
    return selector.show_menu()


def check_ollama_installed():
    """Check if Ollama is installed and running"""
    import subprocess
    try:
        # Try to check if Ollama is installed
        result = subprocess.run(
            ["ollama", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            logger.info(f"[Ollama] Versão instalada: {result.stdout.strip()}")
            print(f"[Ollama] Versão instalada: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    except Exception as e:
        logger.error(f"[Ollama] Erro ao verificar: {e}")
    
    print("\n" + "=" * 60)
    print("⚠️  OLLAMA NÃO ENCONTRADO!")
    print("=" * 60)
    print("\nPara usar IA local, você precisa instalar o Ollama:")
    print("\n1. Acesse: https://ollama.com/download")
    print("2. Baixe e instale o Ollama para Windows")
    print("3. Após instalação, execute: ollama pull llama3.2")
    print("4. Reinicie este aplicativo")
    print("\n" + "=" * 60)
    logger.warning("Ollama não encontrado")
    
    input("\nPressione ENTER para continuar sem IA (modo limitado)...")
    return False


def install_gpu_dependencies(hardware_mode: str):
    """Install GPU-specific dependencies if not already installed"""
    import subprocess
    
    if hardware_mode == "nvidia":
        # Check if CUDA PyTorch is installed
        try:
            import torch
            if torch.cuda.is_available():
                msg = f"[GPU] NVIDIA CUDA disponível: {torch.cuda.get_device_name(0)}"
                print(msg)
                logger.info(msg)
                return
        except ImportError:
            pass
        
        logger.info("[GPU] Instalando PyTorch com CUDA para NVIDIA...")
        print("[GPU] Instalando PyTorch com CUDA para NVIDIA...")
        subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "torch", "torchvision", "torchaudio",
            "--index-url", "https://download.pytorch.org/whl/cu121",
            "-q"
        ], capture_output=True)
        logger.info("[GPU] PyTorch CUDA instalado!")
        print("[GPU] PyTorch CUDA instalado!")
        
    elif hardware_mode == "amd":
        # Check if DirectML is installed
        try:
            import torch_directml
            msg = "[GPU] AMD DirectML já está instalado"
            print(msg)
            logger.info(msg)
            return
        except ImportError:
            pass
        
        logger.info("[GPU] Instalando dependências para AMD GPU (DirectML)...")
        print("[GPU] Instalando dependências para AMD GPU (DirectML)...")
        
        # Install torch-directml for AMD GPUs on Windows
        subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "torch-directml", "-q"
        ], capture_output=True)
        
        # Install ONNX Runtime DirectML
        subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "onnxruntime-directml", "-q"
        ], capture_output=True)
        
        logger.info("[GPU] AMD DirectML instalado!")
        print("[GPU] AMD DirectML instalado!")
        print("[GPU] Sua RX 6650 XT será usada para acelerar a IA!")


def start_backend_server(hardware_mode: str):
    """Inicia o servidor backend em uma thread separada"""
    from src.core.assistant import SkynetAssistant
    from src.server.websocket_server import start_server
    
    async def run_server():
        logger.info("[Skynet Desktop] Inicializando sistemas...")
        print("\n[Skynet Desktop] Inicializando sistemas...")
        assistant = SkynetAssistant()
        
        # Pass hardware mode to AI client
        await assistant.initialize()
        
        # Set hardware mode on AI client if available
        if hasattr(assistant, 'ai') and hasattr(assistant.ai, 'hardware_mode'):
            assistant.ai.hardware_mode = hardware_mode
        
        logger.info("[Skynet Desktop] Servidor backend iniciado")
        print("[Skynet Desktop] Servidor backend iniciado")
        await start_server(assistant)
    
    # Criar novo event loop para esta thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(run_server())
    except Exception as e:
        logger.error(f"[Backend] Erro no servidor: {e}")
        raise


def main():
    print_banner()
    
    # Hardware selection
    hardware_mode = select_hardware()
    logger.info(f"Hardware mode selected: {hardware_mode}")
    
    # Configure environment based on hardware
    from src.core.hardware_selector import HardwareSelector
    selector = HardwareSelector()
    selector.selected_hardware = hardware_mode
    selector.configure_environment()
    
    # Install GPU-specific dependencies if needed
    install_gpu_dependencies(hardware_mode)
    
    # Check if Ollama is installed
    check_ollama_installed()
    
    # Iniciar backend em thread separada
    backend_thread = threading.Thread(
        target=start_backend_server, 
        args=(hardware_mode,),
        daemon=True
    )
    backend_thread.start()
    
    # Aguardar backend inicializar
    import time
    print("[Skynet Desktop] Aguardando servidor backend...")
    logger.info("[Skynet Desktop] Aguardando servidor backend...")
    time.sleep(3)
    
    # Caminho para o frontend
    frontend_path = Path(__file__).parent / "frontend" / "index.html"
    
    if not frontend_path.exists():
        logger.error(f"Frontend não encontrado em: {frontend_path}")
        print(f"[ERRO] Frontend não encontrado em: {frontend_path}")
        sys.exit(1)
    
    # Criar API para comunicação com JavaScript
    api = SkynetAPI()
    
    logger.info("[Skynet Desktop] Abrindo janela...")
    print("[Skynet Desktop] Abrindo janela...")
    print("-" * 60)
    
    # Criar janela do WebView com suporte a transparência
    # Disable transparency to avoid white background issues on some systems
    window = webview.create_window(
        title='SkyNet - Personal AI Assistant',
        url=f'http://localhost:8000',  # Usa o servidor HTTP do backend
        js_api=api,
        width=1280,
        height=800,
        min_size=(800, 600),
        background_color='#000000',
        text_select=False,
        frameless=False,
        easy_drag=False,
        transparent=False  # Disabled to avoid white background issues
    )
    
    # Passar referência da janela para a API
    api.set_window(window)
    
    # Iniciar WebView com GUI específico para evitar erros
    try:
        webview.start(
            debug=False,
            gui='edgechromium',  # Use Edge Chromium backend
            private_mode=False
        )
    except RecursionError as e:
        logger.debug(f"Suppressed pywebview recursion error: {e}")
    except Exception as e:
        logger.error(f"WebView error: {e}")
        raise


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("SkyNet encerrado pelo usuário")
        print("\n[Skynet Desktop] Encerrando... Até logo!")
    except RecursionError as e:
        # Silently ignore recursion errors from pywebview
        logger.debug(f"Main recursion error suppressed: {e}")
    except Exception as e:
        logger.error(f"Erro fatal: {e}", exc_info=True)
        print(f"\n[ERRO] {e}")
        import traceback
        traceback.print_exc()
        input("\nPressione ENTER para sair...")
