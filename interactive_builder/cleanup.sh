#!/bin/bash

echo "🧹 Cleaning up SDD Interactive Builder processes..."

# Kill processes on standard ports
echo "Checking for processes on standard ports..."

# Port 8000 (backend)
BACKEND_PIDS=$(lsof -ti:8000 2>/dev/null)
if [ -n "$BACKEND_PIDS" ]; then
    echo "Killing backend processes on port 8000: $BACKEND_PIDS"
    kill -9 $BACKEND_PIDS 2>/dev/null
    echo "✅ Backend processes (8000) killed"
else
    echo "✅ No backend processes found on port 8000"
fi

# Port 3000 (frontend)  
FRONTEND_PIDS=$(lsof -ti:3000 2>/dev/null)
if [ -n "$FRONTEND_PIDS" ]; then
    echo "Killing frontend processes on port 3000: $FRONTEND_PIDS"
    kill -9 $FRONTEND_PIDS 2>/dev/null
    echo "✅ Frontend processes (3000) killed"
else
    echo "✅ No frontend processes found on port 3000"
fi

# Kill processes on alternative ports
echo "Checking for processes on alternative ports..."

# Port 8001 (alternative backend)
ALT_BACKEND_PIDS=$(lsof -ti:8001 2>/dev/null)
if [ -n "$ALT_BACKEND_PIDS" ]; then
    echo "Killing backend processes on port 8001: $ALT_BACKEND_PIDS"
    kill -9 $ALT_BACKEND_PIDS 2>/dev/null
    echo "✅ Alternative backend processes (8001) killed"
else
    echo "✅ No backend processes found on port 8001"
fi

# Port 3001 (alternative frontend)  
ALT_FRONTEND_PIDS=$(lsof -ti:3001 2>/dev/null)
if [ -n "$ALT_FRONTEND_PIDS" ]; then
    echo "Killing frontend processes on port 3001: $ALT_FRONTEND_PIDS"
    kill -9 $ALT_FRONTEND_PIDS 2>/dev/null
    echo "✅ Alternative frontend processes (3001) killed"
else
    echo "✅ No frontend processes found on port 3001"
fi

echo "🎉 Cleanup complete! All ports should now be available."