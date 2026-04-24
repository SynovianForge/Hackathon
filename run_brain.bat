@echo off
echo =======================================================
echo 🧠 Waking up the Gatekeeper Brain...
echo =======================================================

:: Step 1: Safety Check
if not exist venv\Scripts\activate (
    echo ❌ ERROR: Virtual environment not found! 
    echo Please run init_brain.bat first to set up your environment.
    pause
    exit /b
)

:: Step 2: Activate the environment
echo ⚡ Activating Virtual Environment...
call venv\Scripts\activate

:: Step 3: Launch the Server
echo 🚀 Starting FastAPI Server on http://127.0.0.1:8000
echo 🛑 Press Ctrl+C to stop the server.
echo =======================================================
uvicorn app:app --reload