#!/bin/bash

# SDD Interactive Builder Startup Script

echo "🚀 Starting SDD Interactive Specification Builder..."

# Check if we're in the right directory
if [ ! -d "frontend" ] || [ ! -d "backend" ]; then
    echo "❌ Please run this script from the interactive_builder directory"
    exit 1
fi

# Check for API keys in environment (same as main SDD project)
if [ -z "$OPENAI_API_KEY" ] && [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "⚠️  No AI API keys found in environment"
    echo "📝 Please set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variables"
    echo "    (same as you use for the main SDD project)"
    exit 1
fi

echo "✅ API keys found in environment"

# Function to check if port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo "⚠️  Port $1 is already in use"
        return 1
    fi
    return 0
}

# Check if ports are available
check_port 3000 || { echo "Frontend port 3000 is busy"; exit 1; }
check_port 8000 || { echo "Backend port 8000 is busy"; exit 1; }

echo "✅ Ports available"

# Check if backend dependencies are installed
if [ ! -d "backend/venv" ]; then
    echo "📦 Setting up Python virtual environment..."
    cd backend
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ..
fi

# Check if frontend dependencies are installed
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
fi

echo "🔥 Starting services..."

# Start backend
echo "🐍 Starting backend (Python/FastAPI)..."
cd backend
source venv/bin/activate
python main.py &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 3

# Start frontend
echo "⚛️  Starting frontend (React/Vite)..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "🎉 SDD Interactive Builder is starting up!"
echo ""
echo "📡 Backend API: http://localhost:8000"
echo "🌐 Frontend App: http://localhost:3000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ All services stopped"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Wait for either process to exit
wait