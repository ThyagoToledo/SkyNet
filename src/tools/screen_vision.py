"""
Screen Vision Module
Provides screen capture and analysis using vision models
"""

import asyncio
import base64
import io
import os
from datetime import datetime
from typing import Optional

try:
    from PIL import ImageGrab, Image
except ImportError:
    ImageGrab = None
    Image = None

try:
    import httpx
except ImportError:
    httpx = None


class ScreenVision:
    """Screen capture and vision analysis tools"""
    
    def __init__(self, ollama_base_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_base_url
        self.vision_model = "llava-llama3"  # Modelo com visão
        self.screenshots_dir = os.path.expanduser("~/Pictures/Skynet_Screenshots")
        os.makedirs(self.screenshots_dir, exist_ok=True)
    
    async def capture_screen(self, save: bool = True) -> tuple[Optional[str], Optional[bytes]]:
        """
        Capture the current screen
        
        Args:
            save: Whether to save the screenshot to disk
            
        Returns:
            Tuple of (file_path, image_bytes)
        """
        if not ImageGrab:
            return None, None
        
        try:
            # Capture screen
            screenshot = ImageGrab.grab()
            
            # Convert to bytes
            img_buffer = io.BytesIO()
            screenshot.save(img_buffer, format='PNG')
            img_bytes = img_buffer.getvalue()
            
            file_path = None
            if save:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_path = os.path.join(self.screenshots_dir, f"screen_{timestamp}.png")
                screenshot.save(file_path)
            
            return file_path, img_bytes
            
        except Exception as e:
            print(f"[Vision] Erro ao capturar tela: {e}")
            return None, None
    
    async def analyze_screen(self, question: str = "Descreva o que você vê na tela") -> str:
        """
        Capture screen and analyze it with vision model
        
        Args:
            question: Question about the screen content
            
        Returns:
            Analysis result
        """
        if not ImageGrab:
            return "❌ Erro: Pillow não instalado. Execute: pip install Pillow"
        
        if not httpx:
            return "❌ Erro: httpx não instalado"
        
        try:
            # Capture screen
            file_path, img_bytes = await self.capture_screen(save=True)
            
            if not img_bytes:
                return "❌ Não foi possível capturar a tela"
            
            # Convert to base64
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            
            # Send to vision model
            result = await self._analyze_image_with_ollama(img_base64, question)
            
            if file_path:
                result += f"\n\n📸 Screenshot salvo em: {file_path}"
            
            return result
            
        except Exception as e:
            return f"❌ Erro ao analisar tela: {str(e)}"
    
    async def analyze_image_file(self, image_path: str, question: str = "Descreva esta imagem") -> str:
        """
        Analyze an existing image file
        
        Args:
            image_path: Path to the image file
            question: Question about the image
            
        Returns:
            Analysis result
        """
        if not Image:
            return "❌ Erro: Pillow não instalado"
        
        try:
            # Expand path
            image_path = os.path.expanduser(os.path.expandvars(image_path))
            
            if not os.path.exists(image_path):
                return f"❌ Arquivo não encontrado: {image_path}"
            
            # Load and convert image
            with Image.open(image_path) as img:
                # Convert to PNG bytes
                img_buffer = io.BytesIO()
                img.save(img_buffer, format='PNG')
                img_bytes = img_buffer.getvalue()
            
            # Convert to base64
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            
            # Analyze
            return await self._analyze_image_with_ollama(img_base64, question)
            
        except Exception as e:
            return f"❌ Erro ao analisar imagem: {str(e)}"
    
    async def _analyze_image_with_ollama(self, img_base64: str, question: str) -> str:
        """
        Send image to Ollama vision model for analysis
        
        Args:
            img_base64: Base64 encoded image
            question: Question about the image
            
        Returns:
            Model's analysis
        """
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.vision_model,
                        "prompt": question,
                        "images": [img_base64],
                        "stream": False,
                        "options": {
                            "temperature": 0.3,
                            "num_predict": 512
                        }
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    analysis = result.get("response", "Não consegui analisar a imagem")
                    return f"👁️ **Análise da Imagem:**\n\n{analysis}"
                else:
                    return f"❌ Erro do modelo de visão: HTTP {response.status_code}"
                    
        except httpx.ConnectError:
            return "❌ Ollama não está rodando. Inicie com: ollama serve"
        except Exception as e:
            return f"❌ Erro na análise: {str(e)}"
    
    async def check_vision_model(self) -> bool:
        """Check if vision model is available"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.ollama_url}/api/tags")
                
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    model_names = [m["name"] for m in models]
                    
                    # Check for any vision model
                    vision_models = ["llava", "bakllava", "llava-llama3", "moondream"]
                    for vm in vision_models:
                        if any(vm in name for name in model_names):
                            return True
                    
                return False
                
        except:
            return False


# Singleton instance
screen_vision = ScreenVision()
