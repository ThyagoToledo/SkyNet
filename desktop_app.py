"""
Skynet Desktop Application
Desktop wrapper using PyWebView with audio device management
"""

import asyncio
import os
import sys
import json
import threading
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    import webview
except ImportError:
    print("PyWebView não encontrado. Instalando...")
    os.system(f"{sys.executable} -m pip install pywebview")
    import webview

try:
    import sounddevice as sd
except ImportError:
    print("SoundDevice não encontrado. Instalando...")
    os.system(f"{sys.executable} -m pip install sounddevice")
    import sounddevice as sd

from dotenv import load_dotenv

load_dotenv()


class AudioDeviceManager:
    """Gerencia dispositivos de áudio do sistema"""
    
    def __init__(self):
        self.selected_input = None
        self.selected_output = None
        self.config_file = Path(__file__).parent / "data" / "audio_config.json"
        self.load_config()
    
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
            print(f"Erro ao listar dispositivos de entrada: {e}")
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
            print(f"Erro ao listar dispositivos de saída: {e}")
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
            print(f"Dispositivos configurados: entrada={input_id}, saída={output_id}")
        except Exception as e:
            print(f"Erro ao configurar dispositivos: {e}")
    
    def load_config(self):
        """Carrega configuração salva"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.selected_input = config.get('input')
                    self.selected_output = config.get('output')
                    
                    # Aplicar configuração
                    if self.selected_input or self.selected_output:
                        self.set_devices(self.selected_input, self.selected_output)
        except Exception as e:
            print(f"Erro ao carregar configuração de áudio: {e}")
    
    def save_config(self):
        """Salva configuração"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump({
                    'input': self.selected_input,
                    'output': self.selected_output
                }, f)
        except Exception as e:
            print(f"Erro ao salvar configuração de áudio: {e}")


class SkynetAPI:
    """API exposta para o JavaScript no WebView"""
    
    def __init__(self):
        self.audio_manager = AudioDeviceManager()
        self.server_task = None
        self.assistant = None
    
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
    ║                     Desktop Edition                           ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def start_backend_server():
    """Inicia o servidor backend em uma thread separada"""
    from src.core.assistant import SkynetAssistant
    from src.server.websocket_server import start_server
    
    async def run_server():
        print("\n[Skynet Desktop] Inicializando sistemas...")
        assistant = SkynetAssistant()
        await assistant.initialize()
        
        print("[Skynet Desktop] Servidor backend iniciado")
        await start_server(assistant)
    
    # Criar novo event loop para esta thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_server())


def main():
    print_banner()
    
    # Iniciar backend em thread separada
    backend_thread = threading.Thread(target=start_backend_server, daemon=True)
    backend_thread.start()
    
    # Aguardar backend inicializar
    import time
    print("[Skynet Desktop] Aguardando servidor backend...")
    time.sleep(3)
    
    # Caminho para o frontend
    frontend_path = Path(__file__).parent / "frontend" / "index.html"
    
    if not frontend_path.exists():
        print(f"[ERRO] Frontend não encontrado em: {frontend_path}")
        sys.exit(1)
    
    # Criar API para comunicação com JavaScript
    api = SkynetAPI()
    
    print("[Skynet Desktop] Abrindo janela...")
    print("-" * 60)
    
    # Criar janela do WebView
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
        easy_drag=False
    )
    
    # Iniciar WebView
    webview.start(debug=False)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[Skynet Desktop] Encerrando... Até logo!")
    except Exception as e:
        print(f"\n[ERRO] {e}")
        import traceback
        traceback.print_exc()
