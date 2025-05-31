#!/bin/bash

# SDD Interactive Builder Reset Script

echo "🔄 Resetting SDD Interactive Specification Builder..."

# Check if we're in the right directory
if [ ! -d "frontend" ] || [ ! -d "backend" ]; then
    echo "❌ Please run this script from the interactive_builder directory"
    exit 1
fi

# Clean backend
echo "🧹 Cleaning backend..."
rm -rf backend/venv
rm -rf backend/__pycache__
rm -rf backend/*.pyc

# Clean frontend
echo "🧹 Cleaning frontend..."
rm -rf frontend/node_modules
rm -rf frontend/.next
rm -rf frontend/dist

echo "✨ Clean complete!"
echo ""
echo "Now run ./setup.sh to reinstall everything fresh"