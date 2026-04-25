@echo off
echo =======================================================
echo   Copypasta Hunter - Full Stack Launcher
echo =======================================================

:: Safety Check
if not exist venv\Scripts\activate (
    echo ERROR: Virtual environment not found!
    echo Please run init_brain.bat first.
    pause
    exit /b
)

if not exist node_modules (
    echo ERROR: Probot dependencies not found!
    echo Run: npm install
    pause
    exit /b
)

if not exist frontend\node_modules (
    echo ERROR: Frontend dependencies not found!
    echo Run: cd frontend ^&^& npm install
    pause
    exit /b
)

echo.
echo [1/3] Starting Python Brain on http://127.0.0.1:8000 ...
call venv\Scripts\activate
start "Gatekeeper Brain" cmd /k "call venv\Scripts\activate && uvicorn app:app --host 0.0.0.0 --port 8000 --reload"

echo [2/3] Starting Probot Bot on http://127.0.0.1:3000 ...
start "Copypasta Hunter Bot" cmd /k "npm start"

echo [3/3] Starting Web Interrogation Room on http://localhost:3001 ...
start "Interrogation Room" cmd /k "cd frontend && npm run dev"

echo.
echo =======================================================
echo   All three servers are launching in separate windows.
echo.
echo   Brain API   : http://127.0.0.1:8000
echo   Probot Bot  : http://127.0.0.1:3000
echo   Web UI      : http://localhost:3001
echo.
echo   Close the individual windows to stop each server.
echo =======================================================
pause
