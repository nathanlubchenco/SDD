#!/bin/bash

# SDD Interactive Builder Setup Script

echo "🔧 Setting up SDD Interactive Specification Builder..."

# Check if we're in the right directory
if [ ! -d "frontend" ] || [ ! -d "backend" ]; then
    echo "❌ Please run this script from the interactive_builder directory"
    exit 1
fi

# Check Python version
python_version=$(python3 --version 2>/dev/null | grep -o '[0-9]\+\.[0-9]\+' | head -1)
if [ -z "$python_version" ]; then
    echo "❌ Python 3 not found. Please install Python 3.8 or higher"
    exit 1
fi

# Check Node.js version
node_version=$(node --version 2>/dev/null)
if [ -z "$node_version" ]; then
    echo "❌ Node.js not found. Please install Node.js 16 or higher"
    exit 1
fi

echo "✅ Python version: $(python3 --version)"
echo "✅ Node.js version: $node_version"

# Check for API keys in environment
if [ -z "$OPENAI_API_KEY" ] && [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "⚠️  No AI API keys found in environment"
    echo "📝 Please set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variables"
    echo "    export OPENAI_API_KEY=your_key_here"
    echo "    (same as you use for the main SDD project)"
    exit 1
fi

echo "✅ API keys found in environment"

# Setup backend
echo "🐍 Setting up Python backend..."
cd backend

if [ ! -d "venv" ]; then
    echo "   Creating virtual environment..."
    python3 -m venv venv || {
        echo "❌ Failed to create virtual environment"
        exit 1
    }
fi

echo "   Activating virtual environment..."
source venv/bin/activate || {
    echo "❌ Failed to activate virtual environment"
    exit 1
}

echo "   Installing Python dependencies..."
pip install --upgrade pip

# Try installing from requirements.txt first, fallback to manual installation
echo "   Installing Python dependencies..."
if pip install -r requirements.txt; then
    echo "✅ Dependencies installed from requirements.txt"
else
    echo "⚠️  requirements.txt installation failed, trying manual installation..."
    
    # Install base dependencies
    echo "   Installing base dependencies..."
    pip install -r requirements-base.txt || {
        echo "❌ Failed to install base dependencies"
        exit 1
    }
    
    # Try to install spaCy model
    echo "   Attempting spaCy model installation..."
    python -m spacy download en_core_web_sm || {
        echo "   ⚠️  spaCy model download failed, trying wheel installation..."
        pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.4.1/en_core_web_sm-3.4.1-py3-none-any.whl || {
            echo "   ⚠️  spaCy model installation failed"
            echo "   ✅ Continuing with basic NLP extraction only"
        }
    }
fi

cd ..

# Setup frontend  
echo "⚛️  Setting up React frontend..."
cd frontend

if [ ! -d "node_modules" ]; then
    echo "   Installing Node.js dependencies..."
    npm install || {
        echo "❌ Failed to install Node.js dependencies"
        exit 1
    }
else
    echo "   Node.js dependencies already installed"
    echo "   Updating Node.js dependencies..."
    npm install || {
        echo "⚠️  Failed to update Node.js dependencies - continuing with existing packages"
    }
fi

cd ..

# Validate installation
echo ""
echo "🔍 Validating installation..."

# Check backend dependencies
echo "   Checking Python backend..."
cd backend
source venv/bin/activate
python -c "
import fastapi, uvicorn, socketio, pydantic, openai
print('✅ Core backend dependencies verified')
try:
    import spacy
    try:
        import en_core_web_sm
        print('✅ spaCy with English model verified')
    except ImportError:
        print('⚠️  spaCy installed but English model missing - basic NLP only')
except ImportError:
    print('❌ spaCy installation failed - falling back to basic extraction')
" 2>/dev/null || {
    echo "❌ Backend validation failed"
    exit 1
}
cd ..

# Check frontend dependencies
echo "   Checking frontend..."
cd frontend
if [ -f "node_modules/.bin/vite" ]; then
    echo "✅ Frontend dependencies verified"
else
    echo "❌ Frontend validation failed - Vite not found"
    exit 1
fi
cd ..

echo ""
echo "🎉 Setup complete and validated!"
echo ""
echo "🚀 To start the application:"
echo "  ./start.sh"
echo ""
echo "🧪 To run tests:"
echo "  npm run test:all"
echo ""
echo "🔧 Or manually:"
echo "  # Terminal 1: Backend"
echo "  cd backend && source venv/bin/activate && python main.py"
echo ""  
echo "  # Terminal 2: Frontend"
echo "  cd frontend && npm run dev"
echo ""
echo "📚 Visit http://localhost:3000 when both services are running"
echo ""
echo "🔧 Troubleshooting:"
echo "  • If spaCy model failed to install: Advanced NLP features will be limited"
echo "  • If WebSocket issues occur: Run ./debug.sh for diagnostics"  
echo "  • If port conflicts occur: Use ./start_alt.sh for alternative ports"
echo "  • For test failures: Some tests may not work without spaCy model"
echo ""
echo "💡 For help: Check README.md or run ./debug.sh"