"""
System Controller Module
Provides PC control functionality: open apps, run commands, control UI
"""

import asyncio
import os
import subprocess
import webbrowser
from typing import Optional
import re

class SystemController:
    """Controls system operations like opening apps, running commands, etc."""
    
    def __init__(self):
        # Common application paths on Windows
        self.app_paths = {
            "chrome": [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            ],
            "firefox": [
                r"C:\Program Files\Mozilla Firefox\firefox.exe",
                r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
            ],
            "edge": [
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            ],
            "code": [
                r"C:\Users\%USERNAME%\AppData\Local\Programs\Microsoft VS Code\Code.exe",
                r"C:\Program Files\Microsoft VS Code\Code.exe",
            ],
            "spotify": [
                r"C:\Users\%USERNAME%\AppData\Roaming\Spotify\Spotify.exe",
            ],
            "discord": [
                r"C:\Users\%USERNAME%\AppData\Local\Discord\Update.exe --processStart Discord.exe",
            ],
            "notepad": ["notepad.exe"],
            "calc": ["calc.exe"],
            "explorer": ["explorer.exe"],
            "cmd": ["cmd.exe"],
            "powershell": ["powershell.exe"],
            "terminal": ["wt.exe", "cmd.exe"],  # Windows Terminal or cmd
        }
        
        # App name aliases
        self.app_aliases = {
            "navegador": "chrome",
            "browser": "chrome",
            "google": "chrome",
            "visual studio code": "code",
            "vscode": "code",
            "vs code": "code",
            "música": "spotify",
            "musica": "spotify",
            "bloco de notas": "notepad",
            "calculadora": "calc",
            "arquivos": "explorer",
            "pastas": "explorer",
            "prompt": "cmd",
            "prompt de comando": "cmd",
        }
        
    async def open_application(self, command_text: str) -> str:
        """Open an application based on the command text"""
        command_lower = command_text.lower()
        
        # Extract app name from command
        app_name = None
        
        # Check aliases first
        for alias, app in self.app_aliases.items():
            if alias in command_lower:
                app_name = app
                break
                
        # Check direct app names
        if app_name is None:
            for app in self.app_paths.keys():
                if app in command_lower:
                    app_name = app
                    break
                    
        if app_name is None:
            # Try to extract app name after "abrir"
            match = re.search(r'abrir\s+(?:o\s+)?(.+)', command_lower)
            if match:
                app_name = match.group(1).strip()
                
        if app_name:
            return await self._launch_app(app_name)
        else:
            return "Não consegui identificar qual aplicativo você quer abrir."
            
    async def _launch_app(self, app_name: str) -> str:
        """Launch an application"""
        app_name_lower = app_name.lower()
        
        # Get app paths
        paths = self.app_paths.get(app_name_lower, [])
        
        # Try to find and launch the app
        for path in paths:
            # Expand environment variables
            expanded_path = os.path.expandvars(path)
            
            if os.path.exists(expanded_path) or not os.path.isabs(expanded_path):
                try:
                    # Launch the application
                    if " " in expanded_path and "--" in expanded_path:
                        # Handle complex commands (like Discord)
                        subprocess.Popen(expanded_path, shell=True)
                    else:
                        subprocess.Popen(expanded_path, shell=True)
                        
                    return f"Abrindo {app_name}..."
                except Exception as e:
                    continue
                    
        # Try using 'start' command for system apps
        try:
            subprocess.Popen(f'start {app_name_lower}', shell=True)
            return f"Abrindo {app_name}..."
        except:
            pass
            
        return f"Não consegui encontrar o aplicativo {app_name}."
        
    async def close_application(self, command_text: str) -> str:
        """Close an application"""
        command_lower = command_text.lower()
        
        # Extract app name
        match = re.search(r'fechar\s+(?:o\s+)?(.+)', command_lower)
        if match:
            app_name = match.group(1).strip()
            
            # Map to process name
            process_names = {
                "chrome": "chrome.exe",
                "firefox": "firefox.exe",
                "edge": "msedge.exe",
                "spotify": "Spotify.exe",
                "notepad": "notepad.exe",
                "code": "Code.exe",
                "vscode": "Code.exe",
            }
            
            process_name = process_names.get(app_name.lower(), f"{app_name}.exe")
            
            try:
                subprocess.run(f'taskkill /IM {process_name} /F', shell=True, capture_output=True)
                return f"Fechando {app_name}..."
            except Exception as e:
                return f"Erro ao fechar {app_name}: {str(e)}"
                
        return "Não consegui identificar qual aplicativo você quer fechar."
        
    async def run_command(self, command_text: str) -> str:
        """Run a command in the terminal"""
        # Extract command
        match = re.search(r'(?:executar|rodar|run)\s+(?:comando\s+)?(.+)', command_text.lower())
        if match:
            cmd = match.group(1).strip()
            
            try:
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                output = result.stdout if result.stdout else result.stderr
                if output:
                    return f"Comando executado:\n{output[:500]}"
                else:
                    return "Comando executado com sucesso!"
                    
            except subprocess.TimeoutExpired:
                return "O comando demorou muito para executar."
            except Exception as e:
                return f"Erro ao executar comando: {str(e)}"
                
        return "Não consegui identificar o comando a executar."
        
    async def web_search(self, command_text: str) -> str:
        """Perform a web search"""
        # Extract search query
        match = re.search(r'(?:pesquisar|buscar|procurar)\s+(?:por\s+|sobre\s+)?(.+)', command_text.lower())
        if match:
            query = match.group(1).strip()
            
            # Open search in browser
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            webbrowser.open(search_url)
            
            return f"Pesquisando por: {query}"
            
        return "Não consegui identificar o que você quer pesquisar."
        
    async def set_volume(self, command_text: str) -> str:
        """Set system volume"""
        try:
            import pyautogui
            
            command_lower = command_text.lower()
            
            if any(word in command_lower for word in ["mudo", "mute", "silêncio", "silenciar"]):
                # Mute
                pyautogui.press('volumemute')
                return "Volume mutado."
                
            elif any(word in command_lower for word in ["aumentar", "subir", "mais alto"]):
                # Volume up
                for _ in range(5):
                    pyautogui.press('volumeup')
                return "Volume aumentado."
                
            elif any(word in command_lower for word in ["diminuir", "baixar", "abaixar", "mais baixo"]):
                # Volume down
                for _ in range(5):
                    pyautogui.press('volumedown')
                return "Volume diminuído."
                
            else:
                # Try to extract volume level
                match = re.search(r'(\d+)', command_text)
                if match:
                    level = int(match.group(1))
                    # This is approximate - Windows doesn't have direct volume control via keys
                    return f"Ajustando volume para aproximadamente {level}%..."
                    
        except Exception as e:
            return f"Erro ao ajustar volume: {str(e)}"
            
        return "Não consegui entender o ajuste de volume desejado."
        
    async def take_screenshot(self, command_text: str) -> str:
        """Take a screenshot"""
        try:
            import pyautogui
            from datetime import datetime
            
            # Create screenshots folder
            screenshots_dir = os.path.expanduser("~/Pictures/Skynet_Screenshots")
            os.makedirs(screenshots_dir, exist_ok=True)
            
            # Take screenshot
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(screenshots_dir, f"screenshot_{timestamp}.png")
            
            screenshot = pyautogui.screenshot()
            screenshot.save(filename)
            
            return f"Screenshot salvo em: {filename}"
            
        except Exception as e:
            return f"Erro ao tirar screenshot: {str(e)}"
            
    async def type_text(self, command_text: str) -> str:
        """Type text using keyboard automation"""
        try:
            import pyautogui
            
            # Extract text to type
            match = re.search(r'(?:digitar|escrever|type)\s+(.+)', command_text, re.IGNORECASE)
            if match:
                text = match.group(1).strip()
                
                # Small delay before typing
                await asyncio.sleep(0.5)
                
                pyautogui.write(text, interval=0.05)
                return f"Texto digitado: {text[:50]}..."
                
        except Exception as e:
            return f"Erro ao digitar: {str(e)}"
            
        return "Não consegui identificar o texto a digitar."
        
    async def get_system_info(self) -> dict:
        """Get system information"""
        try:
            import psutil
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_gb": round(memory.used / (1024**3), 2),
                "memory_total_gb": round(memory.total / (1024**3), 2),
                "disk_percent": disk.percent,
                "disk_used_gb": round(disk.used / (1024**3), 2),
                "disk_total_gb": round(disk.total / (1024**3), 2),
            }
            
        except Exception as e:
            return {"error": str(e)}
            
    async def lock_screen(self) -> str:
        """Lock the screen"""
        try:
            subprocess.run('rundll32.exe user32.dll,LockWorkStation', shell=True)
            return "Bloqueando tela..."
        except Exception as e:
            return f"Erro ao bloquear tela: {str(e)}"
            
    async def shutdown(self, command_text: str) -> str:
        """Shutdown or restart the computer"""
        command_lower = command_text.lower()
        
        if "reiniciar" in command_lower or "restart" in command_lower:
            return "Por segurança, não vou reiniciar automaticamente. Use o menu Iniciar."
        elif "desligar" in command_lower or "shutdown" in command_lower:
            return "Por segurança, não vou desligar automaticamente. Use o menu Iniciar."
            
        return "Comando de energia não reconhecido."
    
    # ===========================================
    # NOVAS FUNÇÕES PARA INTEGRAÇÃO COM IA
    # ===========================================
    
    async def execute_smart_command(self, command: str, safe_mode: bool = True) -> str:
        """
        Executa um comando no terminal de forma inteligente.
        
        Args:
            command: O comando a ser executado
            safe_mode: Se True, bloqueia comandos destrutivos
        """
        # Lista de comandos perigosos
        dangerous_commands = [
            "del ", "rm ", "rmdir", "format", "shutdown", "restart",
            "reg delete", "rd /s", "deltree", ":(){", "fork bomb"
        ]
        
        command_lower = command.lower()
        
        # Verificar comandos perigosos
        if safe_mode:
            for dangerous in dangerous_commands:
                if dangerous in command_lower:
                    return f"⚠️ Comando bloqueado por segurança: contém '{dangerous}'. Use safe_mode=False para forçar."
        
        try:
            # Executar comando
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60,
                encoding='utf-8',
                errors='replace'
            )
            
            output = result.stdout if result.stdout else result.stderr
            
            if output:
                # Limitar tamanho da saída
                if len(output) > 1000:
                    output = output[:1000] + "\n... (saída truncada)"
                return f"✅ Comando executado:\n```\n{output}\n```"
            else:
                return "✅ Comando executado com sucesso (sem saída)."
                
        except subprocess.TimeoutExpired:
            return "❌ O comando demorou muito para executar (timeout 60s)."
        except Exception as e:
            return f"❌ Erro ao executar comando: {str(e)}"
    
    async def get_running_processes(self, filter_name: Optional[str] = None) -> str:
        """Lista processos em execução"""
        try:
            import psutil
            
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'cpu_percent']):
                try:
                    info = proc.info
                    if filter_name:
                        if filter_name.lower() not in info['name'].lower():
                            continue
                    processes.append({
                        'pid': info['pid'],
                        'name': info['name'],
                        'memory': round(info['memory_percent'], 1),
                        'cpu': round(info['cpu_percent'], 1)
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Ordenar por memória (decrescente)
            processes.sort(key=lambda x: x['memory'], reverse=True)
            
            # Top 20 processos
            top_processes = processes[:20]
            
            result = "📊 **Processos em Execução (Top 20 por memória):**\n\n"
            result += "| PID | Nome | Memória | CPU |\n"
            result += "|-----|------|---------|-----|\n"
            
            for p in top_processes:
                result += f"| {p['pid']} | {p['name'][:20]} | {p['memory']}% | {p['cpu']}% |\n"
            
            return result
            
        except Exception as e:
            return f"❌ Erro ao listar processos: {str(e)}"
    
    async def file_operations(self, operation: str, path: str, new_path: Optional[str] = None) -> str:
        """
        Operações com arquivos e pastas
        
        Args:
            operation: 'create_folder', 'delete', 'move', 'copy', 'list'
            path: Caminho do arquivo/pasta
            new_path: Novo caminho (para move/copy)
        """
        import shutil
        
        # Expandir variáveis de ambiente e ~
        path = os.path.expanduser(os.path.expandvars(path))
        if new_path:
            new_path = os.path.expanduser(os.path.expandvars(new_path))
        
        try:
            if operation == 'create_folder':
                os.makedirs(path, exist_ok=True)
                return f"✅ Pasta criada: {path}"
                
            elif operation == 'create_file':
                # Criar arquivo vazio
                with open(path, 'w', encoding='utf-8') as f:
                    pass
                return f"✅ Arquivo criado: {path}"
                
            elif operation == 'list':
                if os.path.isdir(path):
                    items = os.listdir(path)
                    result = f"📁 **Conteúdo de {path}:**\n\n"
                    for item in items[:30]:
                        full_path = os.path.join(path, item)
                        if os.path.isdir(full_path):
                            result += f"📁 {item}/\n"
                        else:
                            size = os.path.getsize(full_path)
                            result += f"📄 {item} ({self._format_size(size)})\n"
                    if len(items) > 30:
                        result += f"\n... e mais {len(items) - 30} itens"
                    return result
                else:
                    return f"❌ Caminho não é uma pasta: {path}"
                    
            elif operation == 'move':
                if not new_path:
                    return "❌ Novo caminho não especificado para mover"
                shutil.move(path, new_path)
                return f"✅ Movido de {path} para {new_path}"
                
            elif operation == 'copy':
                if not new_path:
                    return "❌ Novo caminho não especificado para copiar"
                if os.path.isdir(path):
                    shutil.copytree(path, new_path)
                else:
                    shutil.copy2(path, new_path)
                return f"✅ Copiado de {path} para {new_path}"
                
            elif operation == 'delete':
                # Segurança extra para delete
                if os.path.isdir(path):
                    if len(os.listdir(path)) > 0:
                        return f"⚠️ Pasta não está vazia. Use comando direto se quiser deletar: {path}"
                    os.rmdir(path)
                else:
                    os.remove(path)
                return f"✅ Deletado: {path}"
                
            else:
                return f"❌ Operação desconhecida: {operation}"
                
        except PermissionError:
            return f"❌ Permissão negada: {path}"
        except FileNotFoundError:
            return f"❌ Arquivo/pasta não encontrado: {path}"
        except Exception as e:
            return f"❌ Erro: {str(e)}"
    
    def _format_size(self, size: int) -> str:
        """Formata tamanho de arquivo"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    
    async def open_url(self, url: str) -> str:
        """Abre uma URL no navegador padrão"""
        try:
            # Adicionar https:// se não tiver protocolo
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            webbrowser.open(url)
            return f"🌐 Abrindo: {url}"
            
        except Exception as e:
            return f"❌ Erro ao abrir URL: {str(e)}"
    
    async def execute_action(self, action: dict) -> str:
        """
        Executa uma ação recebida da IA
        
        Args:
            action: Dict com 'type' e parâmetros específicos
        """
        action_type = action.get('type', '')
        
        # Import tools on demand to avoid circular imports
        from src.tools.web_search import web_search
        from src.tools.screen_vision import screen_vision
        
        handlers = {
            # Ações de sistema
            'execute_command': lambda: self.execute_smart_command(action.get('command', '')),
            'open_app': lambda: self._launch_app(action.get('app', '')),
            'close_app': lambda: self.close_application(f"fechar {action.get('app', '')}"),
            'open_url': lambda: self.open_url(action.get('url', '')),
            'file_operation': lambda: self.file_operations(
                action.get('operation', ''),
                action.get('path', ''),
                action.get('new_path')
            ),
            'list_processes': lambda: self.get_running_processes(action.get('filter')),
            'set_volume': lambda: self.set_volume(action.get('level', 'aumentar')),
            'screenshot': lambda: self.take_screenshot(''),
            'type_text': lambda: self.type_text(f"digitar {action.get('text', '')}"),
            
            # Ações de pesquisa web
            'web_search': lambda: web_search.search(action.get('query', '')),
            'search_web': lambda: web_search.search(action.get('query', '')),
            'read_page': lambda: web_search.read_webpage(action.get('url', '')),
            'read_webpage': lambda: web_search.read_webpage(action.get('url', '')),
            'youtube_summary': lambda: web_search.get_youtube_transcript(action.get('url', '')),
            'youtube_transcript': lambda: web_search.get_youtube_transcript(action.get('url', '')),
            
            # Ações de visão
            'analyze_screen': lambda: screen_vision.analyze_screen(action.get('question', 'O que você vê na tela?')),
            'see_screen': lambda: screen_vision.analyze_screen(action.get('question', 'Descreva o que está na tela')),
            'analyze_image': lambda: screen_vision.analyze_image_file(action.get('path', ''), action.get('question', 'Descreva esta imagem')),
        }
        
        handler = handlers.get(action_type)
        if handler:
            return await handler()
        else:
            return f"❌ Ação desconhecida: {action_type}"
