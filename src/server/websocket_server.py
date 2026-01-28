"""
WebSocket Server for Skynet
Handles real-time communication between frontend and assistant
"""

import asyncio
import json
import os
from typing import Set, Optional
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"

app = FastAPI(title="Skynet AI Assistant")

# Store for connected clients
connected_clients: Set[WebSocket] = set()

# Reference to assistant (set by start_server)
assistant = None


class ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        print(f"[Server] Client connected. Total: {len(self.active_connections)}")
        
    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        print(f"[Server] Client disconnected. Total: {len(self.active_connections)}")
        
    async def broadcast(self, message: dict):
        """Send message to all connected clients"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"[Server] Error broadcasting: {e}")
                
    async def send_personal(self, websocket: WebSocket, message: dict):
        """Send message to a specific client"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            print(f"[Server] Error sending message: {e}")


manager = ConnectionManager()


# Callback functions for assistant
async def state_callback(state: str, data: dict):
    """Called when assistant state changes"""
    await manager.broadcast({
        "type": "state",
        "state": state,
        "data": data
    })


async def message_callback(message: str, msg_type: str):
    """Called when assistant sends a message"""
    await manager.broadcast({
        "type": "message",
        "content": message,
        "role": msg_type
    })


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication"""
    await manager.connect(websocket)
    
    try:
        # Send welcome message
        await manager.send_personal(websocket, {
            "type": "system",
            "message": "Connected to Skynet"
        })
        
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            await handle_client_message(websocket, data)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"[Server] WebSocket error: {e}")
        manager.disconnect(websocket)


async def handle_client_message(websocket: WebSocket, data: dict):
    """Handle incoming messages from client"""
    msg_type = data.get("type")
    
    if msg_type == "message":
        # Text message from user
        content = data.get("content", "")
        if content and assistant:
            await assistant.process_text_input(content)
            
    elif msg_type == "command":
        action = data.get("action")
        
        if action == "start_listening" and assistant:
            asyncio.create_task(assistant.start_listening())
            
        elif action == "stop_listening" and assistant:
            await assistant.stop_listening()
            
        elif action == "system_info" and assistant:
            info = await assistant.system_control.get_system_info()
            await manager.send_personal(websocket, {
                "type": "system_info",
                "data": info
            })
            
    elif msg_type == "particle":
        # Particle mode change (just acknowledge, frontend handles it)
        mode = data.get("mode")
        await manager.broadcast({
            "type": "particle_mode",
            "mode": mode
        })


@app.post("/api/transcribe")
async def transcribe_audio(audio: UploadFile = File(...)):
    """Transcribe uploaded audio"""
    if assistant and assistant.stt:
        try:
            # Save temporary file
            temp_path = f"/tmp/audio_{audio.filename}"
            
            content = await audio.read()
            with open(temp_path, "wb") as f:
                f.write(content)
                
            # Transcribe
            # Note: This would need audio conversion in production
            text = "Audio transcription would go here"
            
            # Cleanup
            os.unlink(temp_path)
            
            return {"text": text, "success": True}
            
        except Exception as e:
            return {"error": str(e), "success": False}
            
    return {"error": "STT not available", "success": False}


@app.get("/api/status")
async def get_status():
    """Get assistant status"""
    return {
        "status": "online",
        "assistant_state": assistant.current_state if assistant else "unknown"
    }


# Serve frontend static files
@app.get("/")
async def serve_index():
    return FileResponse(FRONTEND_DIR / "index.html")


# Mount static files
app.mount("/js", StaticFiles(directory=str(FRONTEND_DIR / "js")), name="js")
app.mount("/css", StaticFiles(directory=str(FRONTEND_DIR / "css")), name="css")
app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR / "assets")), name="assets")


async def start_server(assistant_instance, host: str = "0.0.0.0", port: int = 8000):
    """Start the WebSocket server with the assistant"""
    global assistant
    assistant = assistant_instance
    
    # Set callbacks
    assistant.set_callbacks(state_callback, message_callback)
    
    # Create necessary directories
    (FRONTEND_DIR / "css").mkdir(exist_ok=True)
    (FRONTEND_DIR / "assets").mkdir(exist_ok=True)
    
    # Configure uvicorn
    config = uvicorn.Config(
        app,
        host=host,
        port=port,
        log_level="info"
    )
    
    server = uvicorn.Server(config)
    
    # Run server
    await server.serve()
