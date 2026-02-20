#!/bin/bash
# Market Intelligence System — Start Script
# Run from the project root: ./start.sh

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "▸ Market Intelligence System Starting..."
echo ""

# ─── Cleanup stale processes ─────────────────────────────────────────────────
echo "Clearing any stale processes on ports 8000 and 3000..."
lsof -ti :8000 | xargs kill -9 2>/dev/null || true
lsof -ti :3000 | xargs kill -9 2>/dev/null || true

# ─── Backend ─────────────────────────────────────────────────────────────────
echo "[1/2] Starting FastAPI backend on http://localhost:8000"
if [ ! -d "$PROJECT_DIR/venv" ]; then
    echo "    Creating Python 3.12 virtualenv..."
    /opt/homebrew/bin/python3.12 -m venv "$PROJECT_DIR/venv"
fi

source "$PROJECT_DIR/venv/bin/activate"

# Install deps if needed
pip install -q -r "$PROJECT_DIR/backend/requirements.txt"

# Start backend in background
cd "$PROJECT_DIR"
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo "    Backend PID: $BACKEND_PID"

# ─── Frontend ────────────────────────────────────────────────────────────────
echo ""
echo "[2/2] Starting Next.js frontend on http://localhost:3000"
cd "$PROJECT_DIR/frontend"

if [ ! -d "node_modules" ]; then
    echo "    Installing npm dependencies..."
    npm install
fi

npm run dev &
FRONTEND_PID=$!
echo "    Frontend PID: $FRONTEND_PID"

# ─── Wait ────────────────────────────────────────────────────────────────────
echo ""
echo "✓ Both servers starting..."
echo ""
echo "  Backend API:   http://localhost:8000"
echo "  API Docs:      http://localhost:8000/docs"
echo "  Frontend:      http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop both servers."
echo ""

# Cleanup on exit
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo 'Servers stopped.'" EXIT INT TERM

wait
