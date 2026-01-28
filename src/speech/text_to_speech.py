"""
Text-to-Speech Module
Provides voice synthesis for the assistant using multiple backends
"""

import asyncio
import os
import tempfile
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class TextToSpeech:
    """Text-to-Speech with multiple backend support"""
    
    def __init__(self):
        self.voice = os.getenv("ASSISTANT_VOICE", "pt-BR-FranciscaNeural")
        self.engine = None
        self.backend = None  # 'edge', 'pyttsx3', 'system'
        
    async def initialize(self):
        """Initialize TTS engine"""
        # Try Edge TTS first (best quality, free)
        try:
            import edge_tts
            self.backend = "edge"
            print("[TTS] Using Edge TTS (Neural voices)")
            return
        except ImportError:
            pass
            
        # Try pyttsx3 (offline)
        try:
            import pyttsx3
            self.engine = pyttsx3.init()
            
            # Configure voice
            voices = self.engine.getProperty('voices')
            for voice in voices:
                if 'brazil' in voice.name.lower() or 'portuguese' in voice.name.lower():
                    self.engine.setProperty('voice', voice.id)
                    break
                    
            self.engine.setProperty('rate', 180)  # Speed
            self.engine.setProperty('volume', 1.0)
            self.backend = "pyttsx3"
            print("[TTS] Using pyttsx3 (System voices)")
            return
        except Exception as e:
            print(f"[TTS] pyttsx3 error: {e}")
            
        # Fallback to system
        self.backend = "system"
        print("[TTS] Using system fallback")
        
    async def speak(self, text: str):
        """Convert text to speech and play"""
        if not text.strip():
            return
            
        try:
            if self.backend == "edge":
                await self._speak_edge(text)
            elif self.backend == "pyttsx3":
                await self._speak_pyttsx3(text)
            else:
                await self._speak_system(text)
        except Exception as e:
            print(f"[TTS] Error speaking: {e}")
            
    async def _speak_edge(self, text: str):
        """Speak using Edge TTS (Microsoft Neural voices)"""
        import edge_tts
        
        # Create temporary file for audio
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            temp_path = f.name
            
        try:
            # Generate speech
            communicate = edge_tts.Communicate(text, self.voice)
            await communicate.save(temp_path)
            
            # Play audio
            await self._play_audio(temp_path)
            
        finally:
            # Cleanup
            try:
                os.unlink(temp_path)
            except:
                pass
                
    async def _speak_pyttsx3(self, text: str):
        """Speak using pyttsx3 (offline)"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._pyttsx3_speak_sync, text)
        
    def _pyttsx3_speak_sync(self, text: str):
        """Synchronous pyttsx3 speech"""
        if self.engine:
            self.engine.say(text)
            self.engine.runAndWait()
            
    async def _speak_system(self, text: str):
        """Fallback using Windows SAPI"""
        try:
            import subprocess
            
            # Use PowerShell to access Windows Speech API
            ps_script = f'''
            Add-Type -AssemblyName System.Speech
            $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
            $synth.Speak("{text.replace('"', "'")}")
            '''
            
            process = await asyncio.create_subprocess_exec(
                'powershell', '-Command', ps_script,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await process.wait()
            
        except Exception as e:
            print(f"[TTS] System fallback error: {e}")
            
    async def _play_audio(self, file_path: str):
        """Play audio file"""
        try:
            import pygame
            
            pygame.mixer.init()
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            
            # Wait for playback to finish
            while pygame.mixer.music.get_busy():
                await asyncio.sleep(0.1)
                
            pygame.mixer.quit()
            
        except ImportError:
            # Fallback to system player
            import subprocess
            
            if os.name == 'nt':
                # Windows
                process = await asyncio.create_subprocess_exec(
                    'cmd', '/c', 'start', '/min', '', file_path,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL
                )
                await process.wait()
                await asyncio.sleep(2)  # Wait for playback
            else:
                # Linux/Mac
                process = await asyncio.create_subprocess_exec(
                    'mpv', '--no-video', file_path,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL
                )
                await process.wait()
                
    async def get_available_voices(self) -> list:
        """Get list of available voices"""
        voices = []
        
        if self.backend == "edge":
            try:
                import edge_tts
                voice_list = await edge_tts.list_voices()
                voices = [
                    {"name": v["ShortName"], "language": v["Locale"]}
                    for v in voice_list
                    if v["Locale"].startswith("pt")
                ]
            except:
                pass
                
        elif self.backend == "pyttsx3" and self.engine:
            voice_list = self.engine.getProperty('voices')
            voices = [
                {"name": v.name, "id": v.id}
                for v in voice_list
            ]
            
        return voices
        
    async def set_voice(self, voice_name: str):
        """Set the voice to use"""
        self.voice = voice_name
        
        if self.backend == "pyttsx3" and self.engine:
            voices = self.engine.getProperty('voices')
            for voice in voices:
                if voice_name.lower() in voice.name.lower():
                    self.engine.setProperty('voice', voice.id)
                    break
                    
    async def cleanup(self):
        """Cleanup resources"""
        if self.engine:
            try:
                self.engine.stop()
            except:
                pass
