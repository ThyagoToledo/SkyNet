"""
Skynet - Personal AI Assistant
Main entry point for the assistant
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.assistant import SkynetAssistant
from src.server.websocket_server import start_server

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
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    print(banner)

async def main():
    print_banner()
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
