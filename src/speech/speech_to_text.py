"""
Speech-to-Text Module using Whisper with GPU acceleration
Supports CPU, NVIDIA CUDA, and AMD DirectML
"""

import asyncio
import os
import sys
import numpy as np
import queue
import threading
from typing import Optional, Callable, Union
from dotenv import load_dotenv

load_dotenv()

class SpeechToText:
    """Speech-to-Text using Whisper with hardware acceleration"""
    
    def __init__(self):
        self.model_name = os.getenv("WHISPER_MODEL", "small")
        self.language = os.getenv("LANGUAGE", "pt")
        self.device = os.getenv("WHISPER_DEVICE", "cpu")  # cpu, cuda, dml
        self.model = None
        self.processor = None
        self.audio_queue = queue.Queue()
        self.is_recording = False
        self.sample_rate = 16000
        self.chunk_duration = 0.3  # seconds (faster chunks for better detection)
        self.silence_threshold = 0.008  # Lower threshold for sensitive detection
        self.silence_duration = 1.2  # seconds of silence to stop (faster response)
        self.min_speech_duration = 0.5  # Minimum speech duration to process
        
        # Callbacks for UI feedback (can be sync or async)
        self.on_speech_start: Optional[Callable[[], Union[None, object]]] = None
        self.on_speech_end: Optional[Callable[[], Union[None, object]]] = None
        self.on_volume_change: Optional[Callable[[float], Union[None, object]]] = None
        
    async def initialize(self):
        """Initialize Whisper model with appropriate hardware acceleration"""
        try:
            print(f"[STT] Loading Whisper model (device: {self.device})...")
            
            # Determine best provider based on device setting
            if self.device == "cuda":
                await self._init_with_cuda()
            elif self.device == "dml":
                await self._init_with_directml()
            else:
                await self._init_with_cpu()
                
        except Exception as e:
            print(f"[STT] Error loading model: {e}")
            print("[STT] Using fallback speech recognition...")
            self.model = None
            
    async def _init_with_cuda(self):
        """Initialize with NVIDIA CUDA acceleration"""
        try:
            import torch
            if torch.cuda.is_available():
                import whisper
                self.model = whisper.load_model(self.model_name, device="cuda")
                self.processor = None
                print(f"[STT] Loaded Whisper {self.model_name} with NVIDIA CUDA")
                return
        except Exception as e:
            print(f"[STT] CUDA initialization failed: {e}")
        
        # Fallback to CPU
        await self._init_with_cpu()
        
    async def _init_with_directml(self):
        """Initialize with AMD DirectML acceleration"""
        try:
            from optimum.onnxruntime import ORTModelForSpeechSeq2Seq
            from transformers import WhisperProcessor
            
            model_id = f"openai/whisper-{self.model_name}"
            
            # Load processor
            self.processor = WhisperProcessor.from_pretrained(model_id)
            
            # Try to load ONNX model with DirectML
            self.model = ORTModelForSpeechSeq2Seq.from_pretrained(
                model_id,
                export=True,
                provider="DmlExecutionProvider"  # AMD GPU via DirectML
            )
            print(f"[STT] Loaded Whisper {self.model_name} with AMD DirectML")
            return
        except ImportError:
            print("[STT] Optimum not available for DirectML")
        except Exception as e:
            print(f"[STT] DirectML initialization failed: {e}")
        
        # Fallback to CPU
        await self._init_with_cpu()
        
    async def _init_with_cpu(self):
        """Initialize with CPU (standard Whisper)"""
        try:
            # Try optimized ONNX first
            try:
                from optimum.onnxruntime import ORTModelForSpeechSeq2Seq
                from transformers import WhisperProcessor
                
                model_id = f"openai/whisper-{self.model_name}"
                self.processor = WhisperProcessor.from_pretrained(model_id)
                self.model = ORTModelForSpeechSeq2Seq.from_pretrained(
                    model_id,
                    export=True,
                    provider="CPUExecutionProvider"
                )
                print(f"[STT] Loaded Whisper {self.model_name} with ONNX CPU optimization")
                return
            except ImportError:
                pass
                
            # Fallback to standard Whisper
            print("[STT] Using standard Whisper (CPU)...")
            import whisper
            self.model = whisper.load_model(self.model_name)
            self.processor = None
            print(f"[STT] Loaded Whisper {self.model_name} model (CPU)")
            
        except Exception as e:
            print(f"[STT] CPU initialization failed: {e}")
            self.model = None
            
    async def listen(self) -> Optional[str]:
        """Listen for audio and return transcribed text"""
        try:
            import sounddevice as sd
            
            # Record audio
            audio_data = await self._record_audio()
            
            if audio_data is None or len(audio_data) == 0:
                return None
                
            # Transcribe
            text = await self._transcribe(audio_data)
            return text
            
        except Exception as e:
            print(f"[STT] Error during listening: {e}")
            return None
            
    async def _record_audio(self) -> Optional[np.ndarray]:
        """Record audio from microphone with voice activity detection"""
        import sounddevice as sd
        
        chunks = []
        silence_chunks = 0
        speech_detected = False
        max_silence_chunks = int(self.silence_duration / self.chunk_duration)
        min_speech_chunks = int(self.min_speech_duration / self.chunk_duration)
        chunk_samples = int(self.sample_rate * self.chunk_duration)
        waiting_chunks = 0
        max_waiting = int(10.0 / self.chunk_duration)  # 10 seconds timeout
        
        print("[STT] Listening...")
        
        try:
            while True:
                # Record chunk
                chunk = sd.rec(
                    chunk_samples,
                    samplerate=self.sample_rate,
                    channels=1,
                    dtype=np.float32
                )
                sd.wait()
                chunk = chunk.flatten()
                
                # Check for voice activity
                volume = np.abs(chunk).mean()
                
                # Notify volume change for UI visualization
                if self.on_volume_change:
                    if asyncio.iscoroutinefunction(self.on_volume_change):
                        await self.on_volume_change(float(volume))
                    else:
                        self.on_volume_change(float(volume))
                
                if volume > self.silence_threshold:
                    # Speech detected!
                    if not speech_detected and self.on_speech_start:
                        if asyncio.iscoroutinefunction(self.on_speech_start):
                            await self.on_speech_start()
                        else:
                            self.on_speech_start()
                    
                    speech_detected = True
                    chunks.append(chunk)
                    silence_chunks = 0
                    waiting_chunks = 0
                    
                elif speech_detected:
                    # Continue recording during brief pauses
                    chunks.append(chunk)
                    silence_chunks += 1
                    
                    # Check if silence duration exceeded (person stopped speaking)
                    if silence_chunks >= max_silence_chunks:
                        if len(chunks) >= min_speech_chunks:
                            # Enough speech recorded, notify end
                            if self.on_speech_end:
                                if asyncio.iscoroutinefunction(self.on_speech_end):
                                    await self.on_speech_end()
                                else:
                                    self.on_speech_end()
                            print("[STT] Speech ended, processing...")
                            break
                        else:
                            # Too short, reset and keep listening
                            chunks = []
                            speech_detected = False
                            silence_chunks = 0
                else:
                    # Waiting for speech
                    waiting_chunks += 1
                    if waiting_chunks >= max_waiting:
                        print("[STT] Timeout waiting for speech")
                        return None
                        
                await asyncio.sleep(0.01)
                
        except Exception as e:
            print(f"[STT] Recording error: {e}")
            return None
            
        if len(chunks) == 0:
            return None
            
        return np.concatenate(chunks)
        
    async def _transcribe(self, audio: np.ndarray) -> Optional[str]:
        """Transcribe audio to text"""
        try:
            if self.processor is not None:
                # Using Optimum/ONNX model
                inputs = self.processor(
                    audio,
                    sampling_rate=self.sample_rate,
                    return_tensors="pt"
                )
                
                generated_ids = self.model.generate(
                    inputs.input_features,
                    language=self.language,
                    task="transcribe"
                )
                
                text = self.processor.batch_decode(
                    generated_ids,
                    skip_special_tokens=True
                )[0]
                
            elif self.model is not None:
                # Using standard Whisper
                import whisper
                
                # Pad/trim audio to 30 seconds
                audio = whisper.pad_or_trim(audio)
                
                # Make log-Mel spectrogram
                mel = whisper.log_mel_spectrogram(audio).to(self.model.device)
                
                # Decode
                options = whisper.DecodingOptions(
                    language=self.language,
                    fp16=False
                )
                result = whisper.decode(self.model, mel, options)
                text = result.text
                
            else:
                # Fallback: Use system speech recognition
                text = await self._fallback_recognition(audio)
                
            return text.strip() if text else None
            
        except Exception as e:
            print(f"[STT] Transcription error: {e}")
            return None
            
    async def _fallback_recognition(self, audio: np.ndarray) -> Optional[str]:
        """Fallback speech recognition using Windows Speech Recognition"""
        try:
            import speech_recognition as sr
            import io
            from scipy.io import wavfile
            
            # Convert to WAV bytes
            buffer = io.BytesIO()
            wavfile.write(buffer, self.sample_rate, (audio * 32767).astype(np.int16))
            buffer.seek(0)
            
            recognizer = sr.Recognizer()
            with sr.AudioFile(buffer) as source:
                audio_data = recognizer.record(source)
                
            # Use Google Speech Recognition (free tier)
            text = recognizer.recognize_google(audio_data, language="pt-BR")
            return text
            
        except Exception as e:
            print(f"[STT] Fallback recognition error: {e}")
            return None
            
    async def cleanup(self):
        """Cleanup resources"""
        self.is_recording = False
        self.model = None
        self.processor = None


class ContinuousListener:
    """Handles continuous listening with wake word detection"""
    
    def __init__(self, stt: SpeechToText, wake_word: str = "skynet"):
        self.stt = stt
        self.wake_word = wake_word.lower()
        self.is_active = False
        self.callback = None
        
    async def start(self, callback):
        """Start continuous listening"""
        self.is_active = True
        self.callback = callback
        
        while self.is_active:
            try:
                text = await self.stt.listen()
                
                if text:
                    text_lower = text.lower()
                    
                    # Check for wake word
                    if self.wake_word in text_lower:
                        # Remove wake word from command
                        command = text_lower.replace(self.wake_word, "").strip()
                        if command and self.callback:
                            await self.callback(command)
                        elif self.callback:
                            await self.callback("")  # Just wake word, await command
                            
            except Exception as e:
                print(f"[Listener] Error: {e}")
                await asyncio.sleep(0.5)
                
    async def stop(self):
        """Stop continuous listening"""
        self.is_active = False
