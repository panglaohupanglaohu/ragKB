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

# Check port availability
check_port() {
    if lsof -ti:$1 &>/dev/null; then
        echo "⚠️  Port $1 is in use. Killing existing process..."
        lsof -ti:$1 | xargs kill -9 2>/dev/null
        sleep 1
    fi
}
check_port 8080
check_port 5173

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
    if ! npm install --silent 2>/dev/null; then
        echo "⚠️  npm install had issues, trying without --silent..."
        npm install
    fi
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

# Wait for backend to be ready
echo "   Waiting for backend..."
for i in $(seq 1 15); do
    if curl -s http://localhost:8080/api/v1/health > /dev/null 2>&1; then
        echo "   ✅ Backend ready"
        break
    fi
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo "   ❌ Backend failed to start. Check logs."
        exit 1
    fi
    sleep 1
done

# Start frontend
echo "🌐 Starting frontend on port 5173..."
npx vite --config vite.config.mjs &
FRONTEND_PID=$!

# Wait for frontend
sleep 2
if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    echo "❌ Frontend failed to start"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

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

cleanup() {
    echo ""
    echo "Shutting down..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    wait $BACKEND_PID 2>/dev/null
    wait $FRONTEND_PID 2>/dev/null
    echo "Done."
    exit 0
}
trap cleanup SIGINT SIGTERM
wait
