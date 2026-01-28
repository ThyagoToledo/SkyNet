"""
Gemini AI Client
Integration with Google's Gemini API for natural language processing
Using the new google-genai SDK
"""

import os
import asyncio
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

class GeminiClient:
    """Client for Google Gemini API using the new google-genai SDK"""
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.client = None
        self.chat = None
        self.model_name = "gemini-2.5-flash"  # Current stable model for free tier
        self.system_prompt = self._get_system_prompt()
        
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the assistant"""
        return """Você é o Skynet, um assistente pessoal de PC inteligente e prestativo.

Suas características:
- Você é amigável, eficiente e direto nas respostas
- Você pode ajudar com tarefas no computador, pesquisas na web e conversas gerais
- Você responde em português brasileiro
- Você tem senso de humor, mas mantém o profissionalismo
- Você é capaz de controlar o computador do usuário quando solicitado

Comandos que você pode executar:
- Abrir aplicativos (Chrome, VS Code, Spotify, etc.)
- Pesquisar na web
- Executar comandos no terminal
- Controlar volume do sistema
- Tirar screenshots
- Digitar texto

Quando o usuário pedir para fazer algo no computador, responda confirmando a ação e seja breve.
Para conversas normais, seja natural e engajado.

Sempre que possível, forneça respostas concisas e úteis."""

    async def initialize(self):
        """Initialize Gemini client"""
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            print("[AI] Warning: Gemini API key not set. Using mock responses.")
            print("[AI] Set GEMINI_API_KEY in .env file to enable AI features.")
            return
            
        try:
            from google import genai
            from google.genai import types
            
            # Create client with API key
            self.client = genai.Client(api_key=self.api_key)
            
            # Create a chat session with system instruction
            self.chat = self.client.chats.create(
                model=self.model_name,
                config=types.GenerateContentConfig(
                    system_instruction=self.system_prompt,
                    temperature=0.7,
                    top_p=0.95,
                    top_k=40,
                    max_output_tokens=1024,
                )
            )
            
            print(f"[AI] Gemini {self.model_name} initialized successfully")
            
        except Exception as e:
            print(f"[AI] Error initializing Gemini: {e}")
            self.client = None
            self.chat = None
            
    async def generate_response(
        self,
        user_message: str,
        conversation_history: List[Dict] = None
    ) -> str:
        """Generate a response using Gemini"""
        
        if self.client is None or self.chat is None:
            return self._mock_response(user_message)
            
        try:
            # Send message using the chat session (maintains history automatically)
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.chat.send_message(user_message)
            )
            
            return response.text
            
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "Resource has been exhausted" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                print(f"[AI] Gemini Rate Limit Exceeded: {e}")
                return "Estou sobrecarregado no momento (limite de uso da API gratuito). Por favor, tente novamente em alguns instantes."
            
            print(f"[AI] Error generating response: {e}")
            return f"Desculpe, ocorreu um erro ao processar sua solicitação: {str(e)}"
            
    def _mock_response(self, user_message: str) -> str:
        """Generate mock response when API is not available"""
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
        return "Entendi sua solicitação. Para respostas mais inteligentes, configure a API do Gemini no arquivo .env"
        
    async def analyze_command(self, text: str) -> Dict:
        """Analyze user text to determine intent and extract parameters"""
        if self.client is None:
            return self._mock_analyze(text)
            
        try:
            from google.genai import types
            
            prompt = f"""Analise o seguinte comando e retorne um JSON com:
- intent: a intenção do usuário (open_app, search_web, run_command, set_volume, general_chat, etc.)
- app_name: nome do aplicativo (se aplicável)
- search_query: termo de busca (se aplicável)
- command: comando a executar (se aplicável)
- response: resposta sugerida para o usuário

Comando: "{text}"

Responda APENAS com o JSON, sem explicações."""

            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt
                )
            )
            
            # Parse JSON response
            import json
            result = json.loads(response.text)
            return result
            
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "Resource has been exhausted" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                print(f"[AI] Gemini Rate Limit Exceeded during command analysis: {e}")
            else:
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
