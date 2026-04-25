#!/bin/bash
echo "======================================================="
echo "  Copypasta Hunter - Full Stack Launcher"
echo "======================================================="

# Safety checks
if [ ! -f "venv/bin/activate" ]; then
    echo "ERROR: Virtual environment not found!"
    echo "Run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

if [ ! -d "node_modules" ]; then
    echo "ERROR: Probot dependencies not found!"
    echo "Run: npm install"
    exit 1
fi

if [ ! -d "frontend/node_modules" ]; then
    echo "ERROR: Frontend dependencies not found!"
    echo "Run: cd frontend && npm install"
    exit 1
fi

echo ""
echo "[1/3] Starting Python Brain on http://127.0.0.1:8000 ..."
source venv/bin/activate
osascript -e 'tell app "Terminal" to do script "cd \"'"$(pwd)"'\" && source venv/bin/activate && uvicorn app:app --host 0.0.0.0 --port 8000"'

echo "[2/3] Starting Probot Bot on http://127.0.0.1:3000 ..."
osascript -e 'tell app "Terminal" to do script "cd \"'"$(pwd)"'\" && npm start"'

echo "[3/3] Starting Web Interrogation Room on http://localhost:3001 ..."
osascript -e 'tell app "Terminal" to do script "cd \"'"$(pwd)"'/frontend\" && npm run dev"'

echo ""
echo "======================================================="
echo "  All three servers are launching in separate tabs."
echo ""
echo "  Brain API   : http://127.0.0.1:8000"
echo "  Probot Bot  : http://127.0.0.1:3000"
echo "  Web UI      : http://localhost:3001"
echo ""
echo "  Close the individual Terminal tabs to stop each server."
echo "======================================================="
