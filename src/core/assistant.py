"""
Skynet Core Assistant Module
Main orchestrator for all assistant functionalities
"""

import asyncio
import os
from typing import Optional, Callable, Dict, Any
from dotenv import load_dotenv

load_dotenv()

class SkynetAssistant:
    """Main assistant class that orchestrates all modules"""
    
    def __init__(self):
        self.name = os.getenv("ASSISTANT_NAME", "Skynet")
        self.is_listening = False
        self.is_speaking = False
        self.is_processing = False
        self.current_state = "idle"  # idle, listening, thinking, speaking
        
        # Module references (initialized later)
        self.stt = None
        self.tts = None
        self.ai = None
        self.system_control = None
        self.memory = None
        
        # Callbacks for frontend
        self.state_callback: Optional[Callable[[str, Dict[str, Any]], Any]] = None
        self.message_callback: Optional[Callable[[str, str], Any]] = None
        
    async def initialize(self):
        """Initialize all assistant modules"""
        print(f"[{self.name}] Loading modules...")
        
        # Import modules
        from src.speech.speech_to_text import SpeechToText
        from src.speech.text_to_speech import TextToSpeech
        from src.ai.ollama_client import OllamaClient
        from src.system.system_controller import SystemController
        from src.memory.memory_manager import MemoryManager
        
        # Initialize modules
        print(f"[{self.name}] Initializing Speech-to-Text (Whisper)...")
        self.stt = SpeechToText()
        await self.stt.initialize()
        
        # Setup STT callbacks for real-time feedback
        self.stt.on_speech_start = self._on_speech_start
        self.stt.on_speech_end = self._on_speech_end
        self.stt.on_volume_change = self._on_volume_change
        
        print(f"[{self.name}] Initializing Text-to-Speech...")
        self.tts = TextToSpeech()
        await self.tts.initialize()
        
        print(f"[{self.name}] Initializing AI (Ollama - Local)...")
        self.ai = OllamaClient()
        await self.ai.initialize()
        
        print(f"[{self.name}] Initializing System Controller...")
        self.system_control = SystemController()
        
        print(f"[{self.name}] Initializing Memory Manager...")
        self.memory = MemoryManager()
        await self.memory.initialize()
        
        print(f"[{self.name}] All systems online!")
        
    def set_callbacks(self, state_callback: Callable[[str, Dict[str, Any]], Any], message_callback: Callable[[str, str], Any]):
        """Set callbacks for frontend communication"""
        self.state_callback = state_callback
        self.message_callback = message_callback
    
    async def _on_speech_start(self):
        """Called when user starts speaking"""
        if self.state_callback:
            await self.state_callback("listening", {"speaking": True})
            
    async def _on_speech_end(self):
        """Called when user stops speaking"""
        await self.update_state("thinking")
        
    async def _on_volume_change(self, volume: float):
        """Called with audio volume level for visualization"""
        if self.state_callback:
            await self.state_callback("listening", {"volume": volume})
        
    async def update_state(self, state: str, data: Optional[Dict[str, Any]] = None):
        """Update assistant state and notify frontend"""
        self.current_state = state
        if self.state_callback:
            await self.state_callback(state, data or {})
            
    async def send_message(self, message: str, msg_type: str = "info"):
        """Send message to frontend"""
        if self.message_callback:
            await self.message_callback(message, msg_type)
            
    async def start_listening(self):
        """Start continuous listening mode"""
        self.is_listening = True
        await self.update_state("listening")
        
        while self.is_listening:
            try:
                # Listen for audio
                text = await self.stt.listen()
                
                if text:
                    await self.process_input(text)
                    
            except Exception as e:
                print(f"[{self.name}] Error during listening: {e}")
                await asyncio.sleep(0.5)
                
    async def stop_listening(self):
        """Stop listening mode"""
        self.is_listening = False
        await self.update_state("idle")
        
    async def process_input(self, text: str):
        """Process user input text"""
        if not text.strip():
            return
            
        print(f"[User] {text}")
        # Note: Frontend already displays user message, so we don't send it again
        
        # Update state to thinking
        await self.update_state("thinking")
        self.is_processing = True
        
        try:
            # Add to memory
            await self.memory.add_message("user", text)
            
            # Get conversation history for context
            history = await self.memory.get_conversation_history()
            
            # Check if it's a system command
            system_response = await self.check_system_command(text)
            
            if system_response:
                response = system_response
            else:
                # Process with AI
                response = await self.ai.generate_response(text, history)
            
            # Add response to memory
            await self.memory.add_message("assistant", response)
            
            print(f"[{self.name}] {response}")
            await self.send_message(response, "assistant")
            
            # Speak the response
            await self.speak(response)
            
        except Exception as e:
            error_msg = f"Desculpe, ocorreu um erro: {str(e)}"
            print(f"[{self.name}] Error: {e}")
            await self.send_message(error_msg, "error")
            await self.speak(error_msg)
            
        finally:
            self.is_processing = False
            await self.update_state("listening" if self.is_listening else "idle")
            
    async def check_system_command(self, text: str) -> Optional[str]:
        """Check if input is a system command and execute it"""
        text_lower = text.lower()
        
        # Define command patterns
        commands = {
            "abrir": self.system_control.open_application,
            "fechar": self.system_control.close_application,
            "executar comando": self.system_control.run_command,
            "pesquisar": self.system_control.web_search,
            "volume": self.system_control.set_volume,
            "screenshot": self.system_control.take_screenshot,
            "digitar": self.system_control.type_text,
        }
        
        for keyword, handler in commands.items():
            if keyword in text_lower:
                try:
                    result = await handler(text)
                    return result
                except Exception as e:
                    return f"Erro ao executar comando: {str(e)}"
                    
        return None
        
    async def speak(self, text: str):
        """Convert text to speech and play with Jarvis-like particle animations"""
        self.is_speaking = True
        await self.update_state("speaking")
        
        # Start particle animation task (Jarvis-style mode switching)
        animation_task = asyncio.create_task(self._animate_particles_while_speaking())
        
        try:
            await self.tts.speak(text)
        finally:
            self.is_speaking = False
            animation_task.cancel()
            try:
                await animation_task
            except asyncio.CancelledError:
                pass
    
    async def _animate_particles_while_speaking(self):
        """Cycle through particle modes while speaking (Jarvis-style)"""
        import random
        modes = ["sphere", "atom", "helix", "wave", "galaxy", "fireworks"]
        
        try:
            while self.is_speaking:
                # Pick a random mode (weighted towards cool ones)
                weights = [0.2, 0.25, 0.2, 0.15, 0.15, 0.05]  # atom/helix more common
                mode = random.choices(modes, weights=weights)[0]
                
                # Send mode change to frontend
                if self.state_callback:
                    await self.state_callback("speaking", {"particle_mode": mode})
                
                # Wait 2-4 seconds before changing again
                wait_time = random.uniform(2.0, 4.0)
                await asyncio.sleep(wait_time)
        except asyncio.CancelledError:
            pass
            
    async def process_text_input(self, text: str):
        """Process text input directly (from web interface)"""
        await self.process_input(text)
        
    async def shutdown(self):
        """Cleanup and shutdown"""
        print(f"[{self.name}] Shutting down...")
        self.is_listening = False
        
        if self.stt:
            await self.stt.cleanup()
        if self.tts:
            await self.tts.cleanup()
        if self.memory:
            await self.memory.cleanup()
            
        print(f"[{self.name}] Goodbye!")
