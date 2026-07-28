#!/bin/bash
echo "=== Zenith Launcher ==="

# Check Python version
if ! command -v python3 &> /dev/null
then
    echo "Error: Python 3 is not installed. Please install Python 3.12+ to play Zenith."
    exit 1
fi

# Set up virtual environment
if [ ! -d ".venv" ] && [ ! -d "venv" ]; then
    echo "Creating virtual environment (.venv)..."
    python3 -m venv .venv
fi

# Activate virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install pygame-ce

# Run game
echo "Launching Zenith..."
python main.py
