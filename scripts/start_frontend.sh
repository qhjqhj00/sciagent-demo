#!/bin/bash

# Get the absolute path of the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
FRONTEND_DIR="$PROJECT_DIR/frontend"
BACKEND_DIR="$PROJECT_DIR/backend"

echo "========================================="
echo "   Starting Research Paper Search App   "
echo "========================================="
echo ""
echo "Frontend directory: $FRONTEND_DIR"
echo "Backend directory: $BACKEND_DIR"
echo ""

# Check if backend process is already running
if pgrep -f "backend/search_app.py" > /dev/null; then
    echo "Backend server is already running"
else
    echo "Starting backend server..."
    cd "$BACKEND_DIR"
    nohup python3 search_app.py > backend.log 2>&1 &
    BACKEND_PID=$!
    echo "Backend started with PID: $BACKEND_PID"
    
    # Wait a bit for backend to start
    sleep 2
fi

# Check if frontend server is already running
if pgrep -f "http.server.*12312" > /dev/null; then
    echo "Frontend server is already running"
else
    echo "Starting frontend server..."
    cd "$FRONTEND_DIR"
    python3 -m http.server 12312 > frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo "Frontend started with PID: $FRONTEND_PID"
fi

echo ""
echo "========================================="
echo "   ✅ Server Started Successfully       "
echo "========================================="
echo ""
echo "📱 Open your browser and visit:"
echo "   http://localhost:12312/index.html"
echo ""
echo "🔧 API endpoints available:"
echo "   http://localhost:12312/api/config"
echo "   http://localhost:12312/api/test_data"
echo "   http://localhost:12312/api/stats"
echo ""
echo "📝 Logs:"
echo "   Backend: $BACKEND_DIR/backend.log"
echo "   Frontend: $FRONTEND_DIR/frontend.log"
echo ""
echo "Press Ctrl+C to stop the servers"
echo ""

# Keep the script running
wait

