#!/bin/bash
# Ramy Sentiment Intelligence - Web Application Launcher
# Linux/macOS Shell Script

echo "========================================"
echo "Ramy Sentiment Intelligence"
echo "Web Application Launcher"
echo "========================================"
echo ""

# Check if virtual environment exists
if [ ! -f ".venv/bin/activate" ]; then
    echo "ERROR: Virtual environment not found!"
    echo "Please create it first: python3 -m venv .venv"
    exit 1
fi

# Activate virtual environment
echo "[1/3] Activating virtual environment..."
source .venv/bin/activate

# Check if dependencies are installed
echo "[2/3] Checking dependencies..."
python -c "import fastapi" 2>/dev/null
if [ $? -ne 0 ]; then
    echo ""
    echo "Dependencies not found. Installing..."
    pip install fastapi==0.109.0 starlette==0.35.1 "pydantic<2" uvicorn jinja2 markupsafe python-multipart pandas numpy
    if [ $? -ne 0 ]; then
        echo ""
        echo "ERROR: Failed to install dependencies!"
        exit 1
    fi
fi

# Start the server
echo "[3/3] Starting web server..."
echo ""
echo "========================================"
echo "Server will start on: http://localhost:8000"
echo "Press CTRL+C to stop the server"
echo "========================================"
echo ""

python -m uvicorn webapp.main:app --host 0.0.0.0 --port 8000

# If server stops
echo ""
echo "Server stopped."
