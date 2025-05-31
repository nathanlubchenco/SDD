#!/bin/bash

# Quick test script for the interactive builder

echo "🧪 Quick Test: SDD Interactive Builder"

# Check environment
echo "Environment check:"
echo "  OPENAI_API_KEY: $([ -n "$OPENAI_API_KEY" ] && echo "✅ Set" || echo "❌ Not set")"
echo "  ANTHROPIC_API_KEY: $([ -n "$ANTHROPIC_API_KEY" ] && echo "✅ Set" || echo "❌ Not set")"

if [ -z "$OPENAI_API_KEY" ] && [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "❌ No API keys found"
    exit 1
fi

cd backend

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "❌ No virtual environment found. Run ./setup.sh first"
    exit 1
fi

source venv/bin/activate

echo ""
echo "🧪 Testing AI client..."
python test_ai.py

if [ $? -eq 0 ]; then
    echo ""
    echo "🚀 Starting backend server..."
    echo "   Press Ctrl+C to stop"
    echo "   Frontend should connect at http://localhost:3000"
    python main.py
else
    echo "❌ AI client test failed. Check your API keys and configuration."
    exit 1
fi