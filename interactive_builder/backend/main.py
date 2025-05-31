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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Socket.IO
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=["http://localhost:3000"],
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
async def connect(sid, environ):
    """Handle client connection"""
    print(f"Client {sid} connected")
    
    # Initialize conversation engine for this session
    if sid not in conversation_sessions:
        conversation_sessions[sid] = ConversationEngine(sid)
    
    # Send welcome message
    await sio.emit('message', {
        'content': "Hi! I'm here to help you build a specification for your system. What would you like to create today?",
        'timestamp': datetime.now().isoformat()
    }, room=sid)

@sio.event
async def disconnect(sid):
    """Handle client disconnection"""
    print(f"Client {sid} disconnected")
    # Optionally clean up session data
    # if sid in conversation_sessions:
    #     del conversation_sessions[sid]

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
    print("📡 WebSocket endpoint: ws://localhost:8000")
    print("🌐 API docs: http://localhost:8000/docs")
    
    uvicorn.run(
        "main:socket_app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )