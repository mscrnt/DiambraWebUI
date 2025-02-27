#!/bin/bash

set -e  # Exit script on any error
clear

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo "[ERROR] Docker is not installed or not in PATH. Please install Docker."
    exit 1
fi

# Check for Python 3.10
if ! python3 --version 2>/dev/null | grep -q "3.10"; then
    echo "[WARNING] Python 3.10 not found. Installing..."
    
    # Install Python 3.10 based on OS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install python@3.10
    elif [[ -x "$(command -v apt-get)" ]]; then
        sudo apt-get update && sudo apt-get install -y python3.10 python3.10-venv
    elif [[ -x "$(command -v yum)" ]]; then
        sudo yum install -y python3.10
    else
        echo "[ERROR] Could not install Python 3.10. Install it manually."
        exit 1
    fi

    # Verify installation
    if ! python3 --version 2>/dev/null | grep -q "3.10"; then
        echo "[ERROR] Python 3.10 installation failed. Please install it manually."
        exit 1
    fi
    echo "[INFO] Python 3.10 installed successfully."
fi

# Create and activate virtual environment silently
if [ ! -d "venv" ]; then
    echo "[INFO] Creating virtual environment..."
    python3.10 -m venv venv > /dev/null 2>&1
fi

source venv/bin/activate

# Install dependencies, suppressing output except for errors
if [ -f "requirements.txt" ]; then
    echo "[INFO] Installing dependencies..."
    pip install -r requirements.txt > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to install dependencies. Check requirements.txt."
        exit 1
    fi
else
    echo "[ERROR] requirements.txt not found!"
    exit 1
fi

# Change to the /app directory
cd "$(dirname "$0")/app"

# Start Docker if it's not running
if ! docker info > /dev/null 2>&1; then
    echo "[INFO] Starting Docker..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open --background -a Docker
    else
        sudo systemctl start docker
    fi
    sleep 10  # Allow Docker to start
fi

# Ensure Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "[ERROR] Docker is not running. Please start Docker manually."
    exit 1
fi

# Find an open port (default to 5000)
PORT=5000
while netstat -an | grep "LISTEN" | grep -q ":$PORT "; do
    echo "[INFO] Port $PORT is in use. Searching for an open port..."
    ((PORT++))
    if [ $PORT -gt 5100 ]; then
        echo "[ERROR] No open ports found! Exiting..."
        exit 1
    fi
done

echo "[INFO] Running Flask on port $PORT"

# Set the environment variable for Flask
export FLASK_PORT=$PORT

# Run Flask
export FLASK_APP=app.py
nohup python -m flask run --host=127.0.0.1 --port=$PORT > flask.log 2>&1 &

# Open browser to Flask site
sleep 3
if which xdg-open > /dev/null; then
    xdg-open "http://127.0.0.1:$PORT"
elif which open > /dev/null; then
    open "http://127.0.0.1:$PORT"
fi

echo "[SUCCESS] Flask server running at http://127.0.0.1:$PORT"
exit 0
