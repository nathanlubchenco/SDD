#!/bin/bash

# SDD Interactive Builder Setup Script

echo "🔧 Setting up SDD Interactive Specification Builder..."

# Check if we're in the right directory
if [ ! -d "frontend" ] || [ ! -d "backend" ]; then
    echo "❌ Please run this script from the interactive_builder directory"
    exit 1
fi

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
    python -m venv venv
fi

echo "   Activating virtual environment..."
source venv/bin/activate

echo "   Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

cd ..

# Setup frontend  
echo "⚛️  Setting up React frontend..."
cd frontend

if [ ! -d "node_modules" ]; then
    echo "   Installing Node.js dependencies..."
    npm install
else
    echo "   Node.js dependencies already installed"
fi

cd ..

echo ""
echo "🎉 Setup complete!"
echo ""
echo "To start the application:"
echo "  ./start.sh"
echo ""
echo "Or manually:"
echo "  # Terminal 1: Backend"
echo "  cd backend && source venv/bin/activate && python main.py"
echo ""  
echo "  # Terminal 2: Frontend"
echo "  cd frontend && npm run dev"