"""
Skynet - Personal AI Assistant
Main entry point for the assistant (Web mode)
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.assistant import SkynetAssistant
from src.server.websocket_server import start_server
from src.core.hardware_selector import HardwareSelector

load_dotenv()

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
    ║                     Local AI - Ollama                         ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def check_ollama():
    """Check if Ollama is installed"""
    import subprocess
    try:
        result = subprocess.run(
            ["ollama", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"[Ollama] Versão: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    except Exception:
        pass
    
    print("\n" + "=" * 60)
    print("⚠️  OLLAMA NÃO ENCONTRADO!")
    print("=" * 60)
    print("\nPara usar IA local, você precisa instalar o Ollama:")
    print("\n1. Acesse: https://ollama.com/download")
    print("2. Baixe e instale o Ollama para Windows")
    print("3. Execute: ollama pull llama3.2")
    print("4. Reinicie este aplicativo")
    print("\n" + "=" * 60)
    input("\nPressione ENTER para continuar (modo limitado)...")
    return False


async def main():
    print_banner()
    
    # Hardware selection
    selector = HardwareSelector()
    hardware = selector.show_menu()
    selector.configure_environment()
    
    # Check Ollama
    check_ollama()
    
    print("\n[Skynet] Initializing systems...")
    
    # Initialize the assistant
    assistant = SkynetAssistant()
    await assistant.initialize()
    
    print("[Skynet] Starting WebSocket server...")
    print("[Skynet] Open http://localhost:8000 in your browser for 3D visualization")
    print("[Skynet] Say 'Skynet' to wake me up!")
    print("-" * 60)
    
    # Start the server (this will also start the assistant)
    await start_server(assistant)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[Skynet] Shutting down... Goodbye!")
