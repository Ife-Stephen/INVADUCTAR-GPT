#!/bin/bash

# Start Python Flask API server in background
echo "Starting Python AI Backend..."
python3 api_server.py &
PYTHON_PID=$!

# Wait a moment for Python server to start
sleep 3

# Start Next.js frontend
echo "Starting Next.js Frontend..."
npm run dev &
NEXTJS_PID=$!

# Function to cleanup processes on exit
cleanup() {
    echo "Shutting down servers..."
    kill $PYTHON_PID 2>/dev/null
    kill $NEXTJS_PID 2>/dev/null
    exit
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

echo "🩺 INVADUCTAR GPT is running!"
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:5000"
echo "Press Ctrl+C to stop both servers"

# Wait for both processes
wait