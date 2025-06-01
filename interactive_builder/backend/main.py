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
from scenario_builder import ScenarioBuilder
from visualization_engine import VisualizationEngine

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

class ScenarioExtractionRequest(BaseModel):
    text: str
    entities: List[str] = []

@app.post("/api/scenarios/extract")
async def extract_scenarios(request: ScenarioExtractionRequest):
    """Extract scenarios from text using real-time scenario builder"""
    try:
        scenario_builder = ScenarioBuilder()
        scenarios = scenario_builder.extract_scenarios_from_text(
            request.text,
            entities=request.entities
        )
        
        # Convert to dictionary format for API response
        result = []
        for scenario in scenarios:
            scenario_dict = scenario_builder.to_dict(scenario)
            result.append(scenario_dict)
        
        return {
            "scenarios": result,
            "count": len(result),
            "extracted_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scenario extraction failed: {str(e)}")

@app.post("/api/scenarios/suggest-completion")
async def suggest_scenario_completion(request: Dict[str, Any]):
    """Suggest completions for partial scenarios"""
    try:
        scenario_builder = ScenarioBuilder()
        
        # Extract current scenario components
        given_text = request.get("given", "")
        when_text = request.get("when", "")
        then_text = request.get("then", "")
        entities = request.get("entities", [])
        
        # Build a text representation
        scenario_text = f"Given {given_text}. When {when_text}. Then {then_text}."
        
        # Extract and analyze
        scenarios = scenario_builder.extract_scenarios_from_text(scenario_text, entities)
        
        if scenarios:
            scenario = scenarios[0]
            suggestions = scenario.completion_suggestions
            validation_issues = scenario.validation_issues
            
            # Also get related scenario suggestions
            related_suggestions = scenario_builder.suggest_related_scenarios(scenario, entities)
            
            return {
                "completion_suggestions": [
                    {
                        "component_type": s.component_type,
                        "suggestion": s.suggestion,
                        "reasoning": s.reasoning,
                        "confidence": s.confidence,
                        "context_entities": s.context_entities
                    }
                    for s in suggestions
                ],
                "validation_issues": validation_issues,
                "related_scenarios": related_suggestions,
                "scenario_confidence": scenario.confidence
            }
        else:
            return {
                "completion_suggestions": [],
                "validation_issues": ["No recognizable scenario pattern found"],
                "related_scenarios": [],
                "scenario_confidence": 0.0
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Suggestion generation failed: {str(e)}")

@app.get("/api/scenarios/templates")
async def get_scenario_templates():
    """Get pre-defined scenario templates"""
    scenario_builder = ScenarioBuilder()
    return {
        "templates": scenario_builder.scenario_templates,
        "domain_patterns": scenario_builder.domain_patterns
    }

# Define visualization types endpoint FIRST (more specific route)
@app.get("/api/visualization/types")
async def get_visualization_types():
    """Get available visualization types and their descriptions"""
    return {
        "types": {
            "entity_relationship": {
                "name": "Entity Relationship Diagram",
                "description": "Shows entities and their relationships",
                "best_for": "Understanding data models and business concepts",
                "min_entities": 1
            },
            "scenario_flow": {
                "name": "Scenario Flow Diagram", 
                "description": "Shows Given/When/Then scenario flows",
                "best_for": "Understanding user journeys and process flows",
                "min_scenarios": 1
            },
            "architecture": {
                "name": "System Architecture Diagram",
                "description": "Shows system components and their interactions",
                "best_for": "Understanding system structure and data flow",
                "min_entities": 2,
                "min_scenarios": 1
            },
            "network": {
                "name": "Network Graph",
                "description": "Shows all entities and relationships as a network",
                "best_for": "Exploring complex interconnections",
                "min_entities": 3
            }
        },
        "auto_selection_rules": {
            "scenarios >= 2": "scenario_flow",
            "entities >= 3": "entity_relationship", 
            "entities >= 1 AND scenarios >= 1": "architecture",
            "default": "entity_relationship"
        }
    }

class VisualizationRequest(BaseModel):
    entities: List[Dict[str, Any]] = []
    scenarios: List[Dict[str, Any]] = []
    constraints: List[Dict[str, Any]] = []
    diagram_type: str = "auto"

@app.post("/api/visualization/generate")
async def generate_custom_visualization(request: VisualizationRequest):
    """Generate visualization from provided data"""
    try:
        visualization_engine = VisualizationEngine()
        
        # Determine diagram type
        diagram_type = request.diagram_type
        if diagram_type == "auto":
            if len(request.scenarios) >= 2:
                diagram_type = "scenario_flow"
            elif len(request.entities) >= 3:
                diagram_type = "entity_relationship"
            elif len(request.entities) >= 1 and len(request.scenarios) >= 1:
                diagram_type = "architecture"
            else:
                diagram_type = "entity_relationship"
        
        # Generate appropriate diagram
        if diagram_type == "entity_relationship":
            diagram = visualization_engine.generate_entity_relationship_diagram(request.entities)
        elif diagram_type == "scenario_flow":
            diagram = visualization_engine.generate_scenario_flow_diagram(request.scenarios, request.entities)
        elif diagram_type == "architecture":
            diagram = visualization_engine.generate_system_architecture_diagram(
                request.entities, request.scenarios, request.constraints
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported diagram type: {diagram_type}")
        
        result = visualization_engine.to_dict(diagram)
        stats = visualization_engine.get_diagram_statistics(diagram)
        
        return {
            "diagram": result,
            "statistics": stats,
            "generated_at": datetime.now().isoformat(),
            "input_summary": {
                "entities": len(request.entities),
                "scenarios": len(request.scenarios), 
                "constraints": len(request.constraints),
                "selected_type": diagram_type
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Custom visualization failed: {str(e)}")

# Session-based visualization endpoint (more general route - define AFTER specific routes)
@app.get("/api/visualization/{session_id}")
async def get_visualization(session_id: str, diagram_type: str = "auto"):
    """Generate visualization for current conversation state"""
    if session_id not in conversation_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        engine = conversation_sessions[session_id]
        diagram = engine.generate_visualization(diagram_type)
        
        return {
            "diagram": diagram,
            "generated_at": datetime.now().isoformat(),
            "session_id": session_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Visualization generation failed: {str(e)}")

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
            
            # Generate and send updated visualization
            try:
                visualization = engine.generate_visualization('auto')
                await sio.emit('visualization_update', {
                    'diagram': visualization,
                    'timestamp': datetime.now().isoformat(),
                    'trigger': 'state_update'
                }, room=sid)
                print(f"📊 Sent real-time visualization update to {sid}")
            except Exception as e:
                print(f"⚠️ Failed to generate visualization update: {e}")
        
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