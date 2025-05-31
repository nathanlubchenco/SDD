# SDD Interactive Specification Builder

An interactive, conversational interface that guides users through discovering and defining their system's behavior. The tool feels like pair programming with a brilliant colleague who asks the right questions, visualizes ideas in real-time, and makes specification writing feel like creative discovery rather than documentation.

## 🌟 Features

- **Progressive Disclosure**: Start simple, reveal complexity as needed
- **Visual Feedback**: See the system emerge as you describe it
- **Conversational Flow**: Natural dialogue, not form filling
- **Instant Gratification**: See working previews as you build
- **Joyful Discovery**: Make finding edge cases feel like treasure hunting

## 🏗️ Architecture

### Frontend (React + TypeScript)
- **Chat Interface**: Natural conversation with AI
- **Visualization Canvas**: Real-time system diagrams
- **Preview Panel**: Live specification preview
- **State Management**: Zustand for reactive state

### Backend (FastAPI + Python)
- **Conversation Engine**: AI-powered dialog management
- **Specification Compiler**: Extract specs from conversation
- **Preview Generator**: Live API mocking
- **AI Orchestrator**: OpenAI/Anthropic integration

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and npm
- Python 3.11+
- OpenAI API key (or Anthropic API key)

### 1. Automated Setup (Recommended)

```bash
cd interactive_builder

# Set your API key first
export OPENAI_API_KEY=your_api_key_here
# or
export ANTHROPIC_API_KEY=your_api_key_here

# Run the automated setup script
./setup.sh
```

### 2. Manual Setup (Alternative)

```bash
cd interactive_builder

# Backend setup
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements-base.txt
python -m spacy download en_core_web_sm  # Optional: for advanced NLP

# Frontend setup
cd ../frontend
npm install
```

### 3. Set Environment Variables

The interactive builder uses the same environment variables as the main SDD project:

```bash
export OPENAI_API_KEY=your_api_key_here
# or
export ANTHROPIC_API_KEY=your_api_key_here
```

Optional configuration:
```bash
export AI_PROVIDER=openai  # or anthropic (defaults to openai)
export OPENAI_MODEL=gpt-4-turbo-preview  # custom model
```

### 4. Start Development Servers

```bash
# Automated startup (recommended)
./start.sh

# Or manually in separate terminals:
# Terminal 1: Start backend
cd backend && source venv/bin/activate && python main.py

# Terminal 2: Start frontend  
cd frontend && npm run dev
```

### 5. Open the Application

Visit `http://localhost:3000` in your browser and start building!

## 🔧 Troubleshooting

### Common Setup Issues

**spaCy Model Installation Failed:**
- Advanced NLP features will be limited but basic extraction still works
- You can manually install: `python -m spacy download en_core_web_sm`

**Port Conflicts:**
- Use alternative ports: `./start_alt.sh` (backend: 8001, frontend: 3001)
- Or manually change ports in configuration files

**WebSocket Connection Issues:**
- Run diagnostics: `./debug.sh`
- Check that both backend and frontend are running
- Verify API keys are set in environment

**Dependency Resolution Problems:**
- Try manual setup instead of automated setup
- Use `requirements-base.txt` for core dependencies only
- Update pip: `pip install --upgrade pip`

## 🎯 Usage Guide

### Phase 1: Discovery
- Describe what you want to build
- AI helps identify entities and relationships
- Natural conversation about system purpose

### Phase 2: Scenario Building
- Define Given/When/Then scenarios
- AI suggests edge cases and alternatives
- Build comprehensive behavior coverage

### Phase 3: Constraint Definition
- Specify performance requirements
- Define security and scalability needs
- Set measurable quality attributes

### Phase 4: Review & Export
- Review complete specification
- Download YAML specification
- Generate implementation (coming soon)

## 🔧 Development

### Frontend Structure
```
frontend/src/
├── components/          # React components
│   ├── ChatInterface.tsx
│   ├── VisualizationCanvas.tsx
│   └── PreviewPanel.tsx
├── store/              # Zustand state management
├── hooks/              # Custom React hooks
├── types/              # TypeScript definitions
└── lib/                # Utilities
```

### Backend Structure
```
backend/
├── main.py             # FastAPI application
├── conversation_engine.py  # AI conversation logic
├── ai_client.py        # OpenAI/Anthropic integration
├── models.py           # Pydantic data models
└── requirements.txt    # Python dependencies
```

### Key Technologies
- **Frontend**: React, TypeScript, Vite, Tailwind CSS, Zustand
- **Backend**: FastAPI, Socket.IO, Pydantic, OpenAI/Anthropic APIs
- **Communication**: WebSocket for real-time updates

## 📈 Progress Tracking

The system tracks progress through:
- **Entities discovered** (30% of score)
- **Scenarios defined** (40% of score)  
- **Constraints specified** (20% of score)
- **Completion bonus** (10% of score)

## 🔮 Coming Soon

- **Interactive Diagrams**: Drag-and-drop system visualization
- **Live API Preview**: Test scenarios in real-time
- **Collaboration**: Multi-user specification building
- **Code Generation**: Direct integration with SDD CLI
- **Templates**: Pre-built specification patterns

## 🧪 Testing

Run tests to verify functionality:

```bash
# Run WebSocket regression tests
npm test

# Run tests in watch mode during development
npm run test:watch

# Manual testing with debug script
./debug.sh
```

### WebSocket Regression Prevention

The project includes comprehensive WebSocket connection regression tests that verify:
- ✅ Backend health and startup
- ✅ Socket.IO handshake functionality  
- ✅ CORS configuration for multiple frontend ports
- ✅ Real-time message exchange
- ✅ Connection state management

These tests run automatically on CI/CD and can be run locally to prevent connection issues.

## 🐛 Troubleshooting

### Backend Issues
- Ensure API keys are set in environment variables (same as main SDD project)
- Check Python version (3.11+ required)
- Verify all dependencies installed

### Frontend Issues  
- Clear npm cache: `npm cache clean --force`
- Delete node_modules and reinstall
- Check Node.js version (18+ required)

### WebSocket Connection Issues
- Ensure backend is running on port 8000
- Check CORS configuration for ports 3000/3001
- Run regression tests: `npm test`
- Use debug script: `./debug.sh`

## 🎨 Customization

### Changing AI Provider
Set environment variables (same as main SDD project):
```bash
export AI_PROVIDER=anthropic
export ANTHROPIC_API_KEY=your_key_here
```

### Styling
Frontend uses Tailwind CSS with custom design tokens in `globals.css`.

### Adding New Phases
1. Add phase to `ConversationPhase` enum in `models.py`
2. Implement phase logic in `conversation_engine.py`
3. Update frontend phase handling

## 📄 License

MIT License - see the main SDD project for details.

## 🤝 Contributing

This is part of the larger SDD research project. Contributions welcome!

1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request

---

**Status**: 🚧 Phase 1 Complete - Core infrastructure and basic chat interface implemented.

The interactive specification builder represents the missing piece that makes SDD truly accessible to all users, regardless of technical expertise.