#!/bin/bash
# Radar Configuration Dashboard - Startup Script (Linux/Mac)

cd "$(dirname "$0")"

echo "Radar Configuration Dashboard - Roma"
echo "======================================"

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Check if dependencies are installed
python3 -c "import flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Run the application
python3 run.py
