#!/bin/bash

echo "🧪 Testing Backend Startup..."

cd backend
source venv/bin/activate

echo "🚀 Starting backend..."
python main.py &
BACKEND_PID=$!

echo "Backend PID: $BACKEND_PID"
echo "Waiting 3 seconds for startup..."
sleep 3

echo "🔍 Testing health endpoint..."
if curl -s http://localhost:8000/api/health >/dev/null 2>&1; then
    echo "✅ Backend health check successful"
else
    echo "❌ Backend health check failed"
fi

echo "🛑 Stopping backend..."
kill $BACKEND_PID 2>/dev/null

cd ..