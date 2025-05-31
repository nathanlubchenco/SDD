import asyncio
import json
import os
from datetime import datetime
from typing import Dict, Any, List

import socketio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

from conversation_engine import ConversationEngine
from models import ConversationState, Message, Entity, Scenario, Constraint

# Initialize FastAPI app
app = FastAPI(title="SDD Interactive Builder Backend", version="1.0.0")

# Get port configuration
PORT = int(os.getenv("PORT", 8000))
FRONTEND_PORT = int(os.getenv("FRONTEND_PORT", 3000))

# Add CORS middleware - Allow both standard and alternative frontend ports
allowed_origins = [
    f"http://localhost:{FRONTEND_PORT}",  # Standard port (3000)
    "http://localhost:3001",             # Alternative port
    "http://localhost:3000",             # Fallback
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Socket.IO
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=allowed_origins,
    logger=True
)

# Combine FastAPI and Socket.IO
socket_app = socketio.ASGIApp(sio, app)

# Global state management (in production, use Redis or database)
conversation_sessions: Dict[str, ConversationEngine] = {}

class MessageRequest(BaseModel):
    content: str

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/conversation/{session_id}/state")
async def get_conversation_state(session_id: str):
    """Get current conversation state"""
    if session_id not in conversation_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    engine = conversation_sessions[session_id]
    return engine.get_state()

@app.post("/api/conversation/{session_id}/reset")
async def reset_conversation(session_id: str):
    """Reset conversation state"""
    if session_id in conversation_sessions:
        conversation_sessions[session_id] = ConversationEngine(session_id)
    else:
        conversation_sessions[session_id] = ConversationEngine(session_id)
    
    return {"status": "reset", "session_id": session_id}

# Socket.IO event handlers
@sio.event
async def connect(sid, environ, auth):
    """Handle client connection"""
    print(f"Client {sid} connected - Current sessions: {list(conversation_sessions.keys())}")
    
    try:
        # Initialize conversation engine for this session
        if sid not in conversation_sessions:
            print(f"Creating new session for {sid}")
            conversation_sessions[sid] = ConversationEngine(sid)
            
            # Send welcome message only for new sessions
            await sio.emit('message', {
                'content': "Hi! I'm here to help you build a specification for your system. What would you like to create today?",
                'timestamp': datetime.now().isoformat()
            }, room=sid)
        else:
            print(f"Session {sid} already exists, skipping welcome message")
        
    except Exception as e:
        print(f"Error during connection setup: {e}")
        await sio.emit('error', {
            'message': 'Failed to initialize conversation engine. Please check server configuration.'
        }, room=sid)

@sio.event
async def disconnect(sid):
    """Handle client disconnection"""
    print(f"Client {sid} disconnected")
    # Clean up session data to prevent memory leaks and duplicate sessions
    if sid in conversation_sessions:
        del conversation_sessions[sid]
        print(f"Cleaned up session for {sid}")

@sio.event
async def message(sid, data):
    """Handle incoming messages from client"""
    try:
        content = data.get('content', '')
        if not content:
            return
        
        print(f"Received message from {sid}: {content}")
        
        # Get or create conversation engine
        if sid not in conversation_sessions:
            conversation_sessions[sid] = ConversationEngine(sid)
        
        engine = conversation_sessions[sid]
        
        # Send typing indicator
        await sio.emit('typing_start', room=sid)
        
        # Process message through conversation engine
        response = await engine.process_message(content)
        
        # Send response
        await sio.emit('typing_end', {
            'content': response['message'],
            'timestamp': datetime.now().isoformat()
        }, room=sid)
        
        # Send updated conversation state
        if response.get('state_updated'):
            await sio.emit('conversation_state_update', engine.get_state(), room=sid)
        
        # Send suggested actions if available
        if response.get('suggested_actions'):
            await sio.emit('suggested_actions', response['suggested_actions'], room=sid)
            
    except Exception as e:
        print(f"Error processing message: {e}")
        await sio.emit('error', {
            'message': 'Sorry, I encountered an error processing your message. Please try again.'
        }, room=sid)

@sio.event
async def typing_start(sid):
    """Handle typing start from client"""
    # Could be used for analytics or multi-user features
    pass

@sio.event
async def typing_end(sid):
    """Handle typing end from client"""
    # Could be used for analytics or multi-user features
    pass

if __name__ == "__main__":
    print("🚀 Starting SDD Interactive Builder Backend...")
    print(f"📡 WebSocket endpoint: ws://localhost:{PORT}")
    print(f"🌐 API docs: http://localhost:{PORT}/docs")
    
    uvicorn.run(
        "main:socket_app",
        host="0.0.0.0",
        port=PORT,
        reload=True,
        log_level="info"
    )