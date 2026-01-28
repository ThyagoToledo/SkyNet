"""
Memory Manager Module
Handles conversation history and long-term memory storage
"""

import asyncio
import os
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

class MemoryManager:
    """Manages short-term and long-term memory for the assistant"""
    
    def __init__(self):
        self.db_path = os.getenv("MEMORY_DB_PATH", "./data/memory.db")
        self.max_history = int(os.getenv("MAX_CONVERSATION_HISTORY", "20"))
        self.connection = None
        
        # Short-term memory (current session)
        self.conversation_history: List[Dict] = []
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    async def initialize(self):
        """Initialize the memory database"""
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Connect to database
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        
        # Create tables
        await self._create_tables()
        
        # Load recent history
        await self._load_recent_history()
        
        print(f"[Memory] Database initialized at {self.db_path}")
        
    async def _create_tables(self):
        """Create database tables"""
        cursor = self.connection.cursor()
        
        # Conversation history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                role TEXT,
                content TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Long-term memory (user preferences, notes, etc.)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE,
                value TEXT,
                category TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Important facts/entities
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity TEXT,
                fact TEXT,
                source TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # User preferences
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE,
                value TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.connection.commit()
        
    async def _load_recent_history(self):
        """Load recent conversation history from database"""
        cursor = self.connection.cursor()
        
        cursor.execute('''
            SELECT role, content, timestamp
            FROM conversations
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (self.max_history,))
        
        rows = cursor.fetchall()
        
        # Reverse to get chronological order
        for row in reversed(rows):
            self.conversation_history.append({
                "role": row["role"],
                "content": row["content"],
                "timestamp": row["timestamp"]
            })
            
    async def add_message(self, role: str, content: str):
        """Add a message to conversation history"""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        # Add to short-term memory
        self.conversation_history.append(message)
        
        # Trim if exceeds max
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]
            
        # Save to database
        cursor = self.connection.cursor()
        cursor.execute('''
            INSERT INTO conversations (session_id, role, content)
            VALUES (?, ?, ?)
        ''', (self.session_id, role, content))
        self.connection.commit()
        
        # Extract and store any important information
        await self._extract_facts(content)
        
    async def get_conversation_history(self, limit: int = None) -> List[Dict]:
        """Get conversation history"""
        limit = limit or self.max_history
        return self.conversation_history[-limit:]
        
    async def _extract_facts(self, text: str):
        """Extract facts from text (simplified version)"""
        # In a real implementation, you might use NLP to extract entities
        # For now, we look for patterns like "my name is X" or "I like Y"
        
        text_lower = text.lower()
        
        patterns = [
            (r"meu nome é (\w+)", "user_name"),
            (r"me chamo (\w+)", "user_name"),
            (r"eu gosto de (.+?)(?:\.|$)", "user_likes"),
            (r"eu prefiro (.+?)(?:\.|$)", "user_preference"),
        ]
        
        import re
        for pattern, key in patterns:
            match = re.search(pattern, text_lower)
            if match:
                value = match.group(1).strip()
                await self.store_preference(key, value)
                
    async def store_memory(self, key: str, value: str, category: str = "general"):
        """Store a memory item"""
        cursor = self.connection.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO memory (key, value, category, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ''', (key, value, category))
        
        self.connection.commit()
        
    async def get_memory(self, key: str) -> Optional[str]:
        """Retrieve a memory item"""
        cursor = self.connection.cursor()
        
        cursor.execute('''
            SELECT value FROM memory WHERE key = ?
        ''', (key,))
        
        row = cursor.fetchone()
        return row["value"] if row else None
        
    async def store_preference(self, key: str, value: str):
        """Store a user preference"""
        cursor = self.connection.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO preferences (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (key, value))
        
        self.connection.commit()
        
    async def get_preference(self, key: str) -> Optional[str]:
        """Get a user preference"""
        cursor = self.connection.cursor()
        
        cursor.execute('''
            SELECT value FROM preferences WHERE key = ?
        ''', (key,))
        
        row = cursor.fetchone()
        return row["value"] if row else None
        
    async def get_all_preferences(self) -> Dict:
        """Get all user preferences"""
        cursor = self.connection.cursor()
        
        cursor.execute('SELECT key, value FROM preferences')
        
        return {row["key"]: row["value"] for row in cursor.fetchall()}
        
    async def add_fact(self, entity: str, fact: str, source: str = "conversation"):
        """Add a fact to the knowledge base"""
        cursor = self.connection.cursor()
        
        cursor.execute('''
            INSERT INTO facts (entity, fact, source)
            VALUES (?, ?, ?)
        ''', (entity, fact, source))
        
        self.connection.commit()
        
    async def get_facts(self, entity: str) -> List[str]:
        """Get facts about an entity"""
        cursor = self.connection.cursor()
        
        cursor.execute('''
            SELECT fact FROM facts WHERE entity = ?
        ''', (entity,))
        
        return [row["fact"] for row in cursor.fetchall()]
        
    async def search_memory(self, query: str) -> List[Dict]:
        """Search through memory"""
        cursor = self.connection.cursor()
        
        # Search in conversations
        cursor.execute('''
            SELECT 'conversation' as type, content as value, timestamp
            FROM conversations
            WHERE content LIKE ?
            ORDER BY timestamp DESC
            LIMIT 10
        ''', (f"%{query}%",))
        
        results = [dict(row) for row in cursor.fetchall()]
        
        # Search in facts
        cursor.execute('''
            SELECT 'fact' as type, fact as value, entity
            FROM facts
            WHERE fact LIKE ? OR entity LIKE ?
            LIMIT 10
        ''', (f"%{query}%", f"%{query}%"))
        
        results.extend([dict(row) for row in cursor.fetchall()])
        
        return results
        
    async def get_context_summary(self) -> str:
        """Get a summary of relevant context for AI"""
        context_parts = []
        
        # User preferences
        preferences = await self.get_all_preferences()
        if preferences:
            pref_str = ", ".join([f"{k}: {v}" for k, v in preferences.items()])
            context_parts.append(f"Preferências do usuário: {pref_str}")
            
        # Recent conversation summary
        if len(self.conversation_history) > 0:
            recent = self.conversation_history[-5:]
            context_parts.append(f"Últimas {len(recent)} mensagens na conversa atual.")
            
        return "\n".join(context_parts) if context_parts else ""
        
    async def clear_session(self):
        """Clear current session history"""
        self.conversation_history = []
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    async def cleanup(self):
        """Cleanup resources"""
        if self.connection:
            self.connection.close()
