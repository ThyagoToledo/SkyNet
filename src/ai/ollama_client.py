"""
Ollama AI Client
Integration with local Ollama instance for natural language processing
Supports CPU, NVIDIA CUDA, and AMD DirectML/ROCm
"""

import asyncio
import json
import os
from typing import List, Dict, Optional

try:
    import httpx
except ImportError:
    httpx = None


class OllamaClient:
    """Client for local Ollama AI"""
    
    def __init__(self, hardware_mode: str = "cpu"):
        self.base_url = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.model_name = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")  # Modelo leve para texto
        self.vision_model = "llava-llama3"  # Modelo pesado só para visão
        self.hardware_mode = hardware_mode
        self.conversation_history: List[Dict] = []
        self.is_available = False
        self.system_prompt = self._get_system_prompt()
        
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the assistant"""
        return """Você é Skynet, assistente de PC inteligente. Responda em português BR.

FERRAMENTAS DISPONÍVEIS (use JSON no final da resposta quando precisar executar):

SISTEMA:
- execute_command: {"actions":[{"type":"execute_command","command":"ipconfig"}]}
- open_app: {"actions":[{"type":"open_app","app":"chrome/spotify/notepad/code"}]}
- open_url: {"actions":[{"type":"open_url","url":"youtube.com"}]}
- file_operation: {"actions":[{"type":"file_operation","operation":"create_folder","path":"~/Desktop/Pasta"}]}
- list_processes: {"actions":[{"type":"list_processes"}]}
- screenshot: {"actions":[{"type":"screenshot"}]}

PESQUISA WEB:
- web_search: {"actions":[{"type":"web_search","query":"python tutorial"}]}
- read_page: {"actions":[{"type":"read_page","url":"https://python.org"}]}
- youtube_summary: {"actions":[{"type":"youtube_summary","url":"youtube.com/watch?v=..."}]}

VISÃO:
- analyze_screen: {"actions":[{"type":"analyze_screen","question":"O que tem na tela?"}]}
- analyze_image: {"actions":[{"type":"analyze_image","path":"caminho/imagem.png","question":"Descreva"}]}

REGRAS:
1. Responda primeiro com uma mensagem, depois inclua JSON se precisar executar algo
2. Não use JSON para conversas normais
3. Seja conciso e útil
4. Para código, forneça explicações claras"""

    async def initialize(self):
        """Initialize Ollama client and check if server is running"""
        print(f"[AI] Inicializando Ollama (modo: {self.hardware_mode})...")
        
        if httpx is None:
            print("[AI] Warning: httpx not installed. Installing...")
            import subprocess
            subprocess.run(["pip", "install", "httpx"], capture_output=True)
            import httpx as hx
            globals()['httpx'] = hx
        
        # Check if Ollama is running
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                
                if response.status_code == 200:
                    self.is_available = True
                    models = response.json().get("models", [])
                    model_names = [m["name"] for m in models]
                    
                    print(f"[AI] Ollama conectado! Modelos disponíveis: {model_names}")
                    
                    # Check if our preferred model is available
                    if not any(self.model_name in name for name in model_names):
                        print(f"[AI] Modelo {self.model_name} não encontrado. Baixando...")
                        await self._pull_model()
                    else:
                        print(f"[AI] Usando modelo: {self.model_name}")
                        
        except Exception as e:
            print(f"[AI] Ollama não está rodando: {e}")
            print("[AI] Para usar IA local, instale Ollama de: https://ollama.com/download")
            print("[AI] Usando respostas mock no momento.")
            self.is_available = False
            
    async def _pull_model(self):
        """Download the model if not available"""
        try:
            print(f"[AI] Baixando modelo {self.model_name}... (isso pode demorar alguns minutos)")
            
            async with httpx.AsyncClient(timeout=600.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/pull",
                    json={"name": self.model_name},
                    timeout=600.0
                )
                
                if response.status_code == 200:
                    print(f"[AI] Modelo {self.model_name} baixado com sucesso!")
                else:
                    print(f"[AI] Erro ao baixar modelo: {response.text}")
                    
        except Exception as e:
            print(f"[AI] Erro ao baixar modelo: {e}")
            
    async def generate_response(
        self,
        user_message: str,
        conversation_history: List[Dict] = None
    ) -> str:
        """Generate a response using Ollama"""
        
        if not self.is_available:
            return self._mock_response(user_message)
            
        try:
            # Build messages list with system prompt and history
            messages = [{"role": "system", "content": self.system_prompt}]
            
            # Add conversation history - menos contexto para mais velocidade
            if conversation_history:
                for msg in conversation_history[-5:]:  # Apenas últimas 5 mensagens
                    messages.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", "")
                    })
            
            # Add current message
            messages.append({"role": "user", "content": user_message})
            
            async with httpx.AsyncClient(timeout=120.0) as client:  # Mais tempo para modelos lentos
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.model_name,
                        "messages": messages,
                        "stream": False,
                        "options": {
                            "temperature": 0.5,  # Mais determinístico = mais rápido
                            "top_p": 0.8,
                            "num_predict": 256,  # Respostas mais curtas
                            "num_ctx": 2048,  # Contexto menor = mais rápido
                        }
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("message", {}).get("content", "Desculpe, não consegui gerar uma resposta.")
                else:
                    print(f"[AI] Erro na resposta: {response.status_code}")
                    return self._mock_response(user_message)
                    
        except Exception as e:
            print(f"[AI] Erro ao gerar resposta: {e}")
            return self._mock_response(user_message)
            
    def _mock_response(self, user_message: str) -> str:
        """Generate mock response when Ollama is not available"""
        user_lower = user_message.lower()
        
        # Basic pattern matching for common commands
        if any(word in user_lower for word in ["olá", "oi", "hey", "bom dia", "boa tarde", "boa noite"]):
            return "Olá! Sou o Skynet, seu assistente pessoal. Como posso ajudar?"
            
        if "abrir" in user_lower:
            app = user_lower.replace("abrir", "").strip()
            return f"Abrindo {app}..."
            
        if "pesquisar" in user_lower or "buscar" in user_lower:
            return "Vou pesquisar isso para você..."
            
        if any(word in user_lower for word in ["como você está", "tudo bem"]):
            return "Estou funcionando perfeitamente! E você, como posso ajudar hoje?"
            
        if "obrigado" in user_lower or "valeu" in user_lower:
            return "De nada! Estou aqui para ajudar."
            
        if any(word in user_lower for word in ["quem é você", "qual seu nome"]):
            return "Sou o Skynet, seu assistente pessoal de PC. Posso ajudar com tarefas no computador, pesquisas e muito mais!"
            
        # Default response
        return "Por favor, instale o Ollama de https://ollama.com/download para respostas completas de IA."
        
    async def analyze_command(self, text: str) -> Dict:
        """Analyze user text to determine intent and extract parameters"""
        if not self.is_available:
            return self._mock_analyze(text)
            
        try:
            prompt = f"""Analise o seguinte comando e retorne um JSON com:
- intent: a intenção do usuário (open_app, search_web, run_command, set_volume, general_chat, etc.)
- app_name: nome do aplicativo (se aplicável)
- search_query: termo de busca (se aplicável)
- command: comando a executar (se aplicável)
- response: resposta sugerida para o usuário

Comando: "{text}"

Responda APENAS com o JSON válido, sem explicações ou texto adicional."""

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model_name,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json"
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    text_response = result.get("response", "{}")
                    return json.loads(text_response)
                    
        except Exception as e:
            print(f"[AI] Error analyzing command: {e}")
            
        return self._mock_analyze(text)
            
    def _mock_analyze(self, text: str) -> Dict:
        """Mock command analysis"""
        text_lower = text.lower()
        
        if "abrir" in text_lower:
            app_keywords = {
                "chrome": "chrome",
                "navegador": "chrome",
                "firefox": "firefox",
                "spotify": "spotify",
                "música": "spotify",
                "code": "code",
                "vscode": "code",
                "visual studio": "code",
                "bloco de notas": "notepad",
                "notepad": "notepad",
                "calculadora": "calc",
                "explorador": "explorer",
                "terminal": "cmd",
                "cmd": "cmd",
                "powershell": "powershell",
            }
            
            for keyword, app in app_keywords.items():
                if keyword in text_lower:
                    return {
                        "intent": "open_app",
                        "app_name": app,
                        "response": f"Abrindo {keyword}..."
                    }
                    
        if "pesquisar" in text_lower or "buscar" in text_lower:
            query = text_lower.replace("pesquisar", "").replace("buscar", "").strip()
            return {
                "intent": "search_web",
                "search_query": query,
                "response": f"Pesquisando: {query}"
            }
            
        return {
            "intent": "general_chat",
            "response": None
        }
    
    def set_model(self, model_name: str):
        """Change the AI model"""
        self.model_name = model_name
        print(f"[AI] Modelo alterado para: {model_name}")
    
    def parse_response_with_actions(self, response: str) -> dict:
        """
        Parse da resposta da IA para extrair ações
        
        Returns:
            dict com 'message' (texto para usuário) e 'actions' (lista de ações)
        """
        import re
        
        result = {
            'message': response,
            'actions': []
        }
        
        # Procura por JSON de ações na resposta
        # Padrão: ```json\n{"actions": [...]}\n```
        json_pattern = r'```json\s*\n?({.+?})\s*\n?```'
        match = re.search(json_pattern, response, re.DOTALL)
        
        if match:
            try:
                action_data = json.loads(match.group(1))
                
                if 'actions' in action_data:
                    result['actions'] = action_data['actions']
                    
                # Remover o JSON da mensagem para o usuário
                result['message'] = re.sub(json_pattern, '', response, flags=re.DOTALL).strip()
                
            except json.JSONDecodeError as e:
                print(f"[AI] Erro ao parsear ações: {e}")
        
        # Fallback: tentar encontrar JSON sem code blocks
        if not result['actions']:
            simple_json_pattern = r'\{\s*"actions"\s*:\s*\[.+?\]\s*\}'
            match = re.search(simple_json_pattern, response, re.DOTALL)
            
            if match:
                try:
                    action_data = json.loads(match.group(0))
                    result['actions'] = action_data.get('actions', [])
                    result['message'] = re.sub(simple_json_pattern, '', response, flags=re.DOTALL).strip()
                except:
                    pass
        
        return result
