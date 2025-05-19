#!/bin/bash

# Enter project directory
cd "$(dirname "$0")"

# Check Python environment
if command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v python &>/dev/null; then
    PYTHON=python
else
    echo "Error: Python interpreter not found. Please install Python 3.8 or higher."
    exit 1
fi

# Check dependencies
echo "Checking dependencies..."
if ! $PYTHON -c "import streamlit" &>/dev/null; then
    echo "Installing dependencies..."
    $PYTHON -m pip install -r requirements.txt
fi

# Start application
echo "Starting RiverInfos application..."
$PYTHON -m streamlit run app.py