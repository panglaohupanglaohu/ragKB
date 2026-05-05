#!/bin/bash
# AgentsGroup2026 — Quick Start Script
set -e

cd "$(dirname "$0")"

echo "🚀 AgentsGroup2026 Starting..."
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python 3.11+"
    exit 1
fi

# Create venv if needed
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

# Install Python deps
echo "📦 Installing Python dependencies..."
pip install -q fastapi uvicorn[standard] pydantic httpx 2>/dev/null || pip install fastapi uvicorn pydantic httpx

# Install Node deps
if [ ! -d "node_modules" ]; then
    echo "📦 Installing Node dependencies..."
    npm install --silent 2>/dev/null || true
fi

echo ""
echo "✅ Dependencies ready"
echo ""

# Start backend
echo "🔧 Starting backend on port 8080..."
cd src/backend
python main.py --port 8080 &
BACKEND_PID=$!
cd ../..

# Wait for backend
sleep 2

# Start frontend
echo "🌐 Starting frontend on port 5173..."
npx vite --config vite.config.mjs &
FRONTEND_PID=$!

echo ""
echo "════════════════════════════════════════"
echo "  AgentsGroup2026 is running!"
echo ""
echo "  Frontend: http://localhost:5173"
echo "  Backend:  http://localhost:8080"
echo "  API Docs: http://localhost:8080/docs"
echo "════════════════════════════════════════"
echo ""
echo "Press Ctrl+C to stop all services"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" SIGINT SIGTERM
wait
