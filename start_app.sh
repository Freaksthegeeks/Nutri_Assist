#!/bin/bash

echo "🥗 Starting Nutrition Assistant Dashboard..."
echo "====================================="
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    echo "Please install Python 3 from https://python.org"
    exit 1
fi

# Check if required packages are installed
echo "📦 Checking dependencies..."
if ! python3 -c "import streamlit" &> /dev/null; then
    echo "⚠️ Dependencies not found. Installing..."
    python3 install_dependencies.py
    echo
fi

# Start the Streamlit app
echo "🚀 Starting Nutrition Assistant..."
echo
echo "💡 The app will open in your default browser"
echo "🛑 Press Ctrl+C to stop the server"
echo

streamlit run app.py