"""
Web Search Module
Provides web search, page reading, and YouTube transcript functionality
"""

import asyncio
import re
from typing import Optional, List, Dict
from bs4 import BeautifulSoup

try:
    from duckduckgo_search import DDGS
except ImportError:
    try:
        from ddgs import DDGS
    except ImportError:
        DDGS = None

try:
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:
    YouTubeTranscriptApi = None

try:
    import httpx
except ImportError:
    httpx = None


class WebSearch:
    """Web search and content extraction tools"""
    
    def __init__(self):
        self.ddgs = DDGS() if DDGS else None
        
    async def search(self, query: str, max_results: int = 5) -> str:
        """
        Search the web using DuckDuckGo
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            Formatted search results
        """
        if not self.ddgs:
            return "❌ Erro: duckduckgo-search não instalado. Execute: pip install duckduckgo-search"
        
        try:
            # Run in thread pool since ddgs is synchronous
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                lambda: list(self.ddgs.text(query, max_results=max_results))
            )
            
            if not results:
                return f"🔍 Nenhum resultado encontrado para: {query}"
            
            output = f"🔍 **Resultados para: {query}**\n\n"
            
            for i, r in enumerate(results, 1):
                title = r.get('title', 'Sem título')
                url = r.get('href', r.get('link', ''))
                snippet = r.get('body', r.get('snippet', ''))[:200]
                
                output += f"**{i}. {title}**\n"
                output += f"   🔗 {url}\n"
                output += f"   {snippet}...\n\n"
            
            return output
            
        except Exception as e:
            return f"❌ Erro na pesquisa: {str(e)}"
    
    async def read_webpage(self, url: str, max_chars: int = 3000) -> str:
        """
        Read and extract text content from a webpage
        
        Args:
            url: URL to read
            max_chars: Maximum characters to return
            
        Returns:
            Extracted text content
        """
        if not httpx:
            return "❌ Erro: httpx não instalado"
        
        try:
            # Add https if missing
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                response = await client.get(url, headers=headers)
                
                if response.status_code != 200:
                    return f"❌ Erro ao acessar página: HTTP {response.status_code}"
                
                # Parse HTML
                soup = BeautifulSoup(response.text, 'lxml')
                
                # Remove script and style elements
                for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                    element.decompose()
                
                # Get text
                text = soup.get_text(separator='\n', strip=True)
                
                # Clean up whitespace
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                text = '\n'.join(lines)
                
                # Truncate if needed
                if len(text) > max_chars:
                    text = text[:max_chars] + "\n\n... (conteúdo truncado)"
                
                return f"📄 **Conteúdo de {url}:**\n\n{text}"
                
        except Exception as e:
            return f"❌ Erro ao ler página: {str(e)}"
    
    async def get_youtube_transcript(self, url_or_id: str) -> str:
        """
        Get transcript/captions from a YouTube video
        
        Args:
            url_or_id: YouTube URL or video ID
            
        Returns:
            Video transcript
        """
        if not YouTubeTranscriptApi:
            return "❌ Erro: youtube-transcript-api não instalado. Execute: pip install youtube-transcript-api"
        
        try:
            # Extract video ID from URL
            video_id = self._extract_youtube_id(url_or_id)
            
            if not video_id:
                return f"❌ Não consegui extrair o ID do vídeo de: {url_or_id}"
            
            # Get transcript (try Portuguese first, then English, then any)
            loop = asyncio.get_event_loop()
            
            transcript = None
            for lang in ['pt', 'pt-BR', 'en', 'en-US']:
                try:
                    transcript = await loop.run_in_executor(
                        None,
                        lambda l=lang: YouTubeTranscriptApi.get_transcript(video_id, languages=[l])
                    )
                    break
                except:
                    continue
            
            # If no specific language found, try to get any available
            if not transcript:
                try:
                    transcript_list = await loop.run_in_executor(
                        None,
                        lambda: YouTubeTranscriptApi.list_transcripts(video_id)
                    )
                    transcript = await loop.run_in_executor(
                        None,
                        lambda: transcript_list.find_transcript(['pt', 'pt-BR', 'en', 'en-US']).fetch()
                    )
                except:
                    # Last resort: get any available transcript
                    transcript = await loop.run_in_executor(
                        None,
                        lambda: YouTubeTranscriptApi.get_transcript(video_id)
                    )
            
            if not transcript:
                return f"❌ Nenhuma legenda/transcrição disponível para este vídeo"
            
            # Combine transcript segments
            full_text = ' '.join([seg['text'] for seg in transcript])
            
            # Limit length
            if len(full_text) > 4000:
                full_text = full_text[:4000] + "... (transcrição truncada)"
            
            return f"🎬 **Transcrição do vídeo ({video_id}):**\n\n{full_text}"
            
        except Exception as e:
            return f"❌ Erro ao obter transcrição: {str(e)}"
    
    def _extract_youtube_id(self, url_or_id: str) -> Optional[str]:
        """Extract YouTube video ID from URL or return ID if already an ID"""
        
        # If it's already just an ID (11 characters, alphanumeric with - and _)
        if re.match(r'^[\w-]{11}$', url_or_id):
            return url_or_id
        
        # Extract from various YouTube URL formats
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/v\/)([^&\n?#]+)',
            r'youtube\.com\/shorts\/([^&\n?#]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url_or_id)
            if match:
                return match.group(1)
        
        return None
    
    async def search_and_summarize(self, query: str) -> str:
        """
        Search the web and provide a summary of findings
        
        Args:
            query: Search query
            
        Returns:
            Search results with brief content from top results
        """
        # First, get search results
        search_results = await self.search(query, max_results=3)
        
        return search_results


# Singleton instance
web_search = WebSearch()
