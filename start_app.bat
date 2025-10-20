@echo off
echo 🥗 Starting Nutrition Assistant Dashboard...
echo =====================================
echo.

REM Set environment variables to suppress TensorFlow warnings
set TF_ENABLE_ONEDNN_OPTS=0

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

REM Check if required packages are installed
echo 📦 Checking dependencies...
python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo ⚠️ Dependencies not found. Installing...
    python install_dependencies.py
    echo.
)

REM Start the Streamlit app
echo 🚀 Starting Nutrition Assistant...
echo.
echo 💡 The app will open in your default browser
echo 🛑 Press Ctrl+C to stop the server
echo.
streamlit run app.py

pause