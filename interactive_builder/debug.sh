#!/bin/bash

# SDD Interactive Builder Debug Script

echo "🔍 Debugging SDD Interactive Builder Connection Issues..."

# Check if we're in the right directory
if [ ! -d "frontend" ] || [ ! -d "backend" ]; then
    echo "❌ Please run this script from the interactive_builder directory"
    exit 1
fi

echo ""
echo "🔍 Environment Check:"
echo "   OPENAI_API_KEY: $([ -n "$OPENAI_API_KEY" ] && echo "✅ Set" || echo "❌ Not set")"
echo "   ANTHROPIC_API_KEY: $([ -n "$ANTHROPIC_API_KEY" ] && echo "✅ Set" || echo "❌ Not set")"
echo "   AI_PROVIDER: ${AI_PROVIDER:-"default (openai)"}"

echo ""
echo "🔍 Backend Check:"
if [ -d "backend/venv" ]; then
    echo "   Virtual environment: ✅ Exists"
    cd backend
    source venv/bin/activate
    
    echo "   Testing Python imports..."
    python -c "
import sys
print(f'   Python version: {sys.version.split()[0]}')

try:
    import socketio
    print('   socketio: ✅ Available')
except ImportError:
    print('   socketio: ❌ Missing')

try:
    import fastapi
    print('   fastapi: ✅ Available')
except ImportError:
    print('   fastapi: ❌ Missing')

try:
    sys.path.append('../../')
    from src.core.ai_client import get_current_config
    config = get_current_config()
    print(f'   SDD AI client: ✅ Available ({config[\"provider\"]})')
except Exception as e:
    print(f'   SDD AI client: ⚠️  Issue ({e})')
"
    cd ..
else
    echo "   Virtual environment: ❌ Missing"
fi

echo ""
echo "🔍 Frontend Check:"
if [ -d "frontend/node_modules" ]; then
    echo "   Node modules: ✅ Installed"
    cd frontend
    echo "   Node version: $(node --version)"
    echo "   npm version: $(npm --version)"
    cd ..
else
    echo "   Node modules: ❌ Missing"
fi

echo ""
echo "🔍 Port Check (Alternative Ports):"
if lsof -Pi :8001 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "   Port 8001: ⚠️  Already in use"
    echo "   Process using port 8001:"
    lsof -Pi :8001 -sTCP:LISTEN
else
    echo "   Port 8001: ✅ Available"
fi

if lsof -Pi :3001 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "   Port 3001: ⚠️  Already in use"
    echo "   Process using port 3001:"
    lsof -Pi :3001 -sTCP:LISTEN
else
    echo "   Port 3001: ✅ Available"
fi

echo "   Standard port check:"
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "   Port 8000: ⚠️  Already in use"
else
    echo "   Port 8000: ✅ Available"
fi

if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "   Port 3000: ⚠️  Already in use"
else
    echo "   Port 3000: ✅ Available"
fi

echo ""
echo "🔍 AI Client Test:"
if [ -d "backend/venv" ]; then
    cd backend
    source venv/bin/activate
    echo "   Testing AI client..."
    if python test_ai.py; then
        echo "   AI client test: ✅ Success"
    else
        echo "   AI client test: ❌ Failed"
    fi
    cd ..
else
    echo "   AI client test: ❌ Skipped (no venv)"
fi

echo ""
echo "🔍 Quick Backend Test (Port 8001):"
if [ -d "backend/venv" ]; then
    cd backend
    source venv/bin/activate
    echo "   Starting backend on port 8001 for 5 seconds..."
    
    # Use gtimeout on macOS, timeout on Linux
    if command -v gtimeout >/dev/null 2>&1; then
        TIMEOUT_CMD="gtimeout 5s"
    elif command -v timeout >/dev/null 2>&1; then
        TIMEOUT_CMD="timeout 5s"
    else
        echo "   ⚠️  timeout command not available, starting backend manually..."
        PORT=8001 python main.py &
        BACKEND_PID=$!
    fi
    
    if [ -n "$TIMEOUT_CMD" ]; then
        PORT=8001 $TIMEOUT_CMD python main.py &
        BACKEND_PID=$!
    fi
    
    sleep 2
    
    echo "   Testing backend connection on port 8001..."
    if curl -s http://localhost:8001/api/health >/dev/null 2>&1; then
        echo "   Backend health check: ✅ Success"
    else
        echo "   Backend health check: ❌ Failed"
        echo "   Testing standard port 8000..."
        if curl -s http://localhost:8000/api/health >/dev/null 2>&1; then
            echo "   Standard port health check: ✅ Success"
        else
            echo "   Standard port health check: ❌ Failed"
        fi
    fi
    
    kill $BACKEND_PID 2>/dev/null
    wait $BACKEND_PID 2>/dev/null
    cd ..
else
    echo "   Backend test: ❌ Skipped (no venv)"
fi

echo ""
echo "🔧 Recommendations:"

if [ -z "$OPENAI_API_KEY" ] && [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "   1. Set API keys: export OPENAI_API_KEY=your_key"
fi

if [ ! -d "backend/venv" ]; then
    echo "   2. Run setup: ./setup.sh"
fi

if [ ! -d "frontend/node_modules" ]; then
    echo "   3. Install frontend: cd frontend && npm install"
fi

echo ""
echo "📚 Next steps:"
echo "   1. Fix any issues above"
echo "   2. Run: ./setup.sh (if needed)"
echo "   3. Run: ./start.sh"
echo "   4. Check browser console for WebSocket errors"