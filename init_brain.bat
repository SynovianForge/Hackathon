@echo off
echo =======================================================
echo 🧠 Pop Quiz Gatekeeper: Dev 1 Environment Setup
echo =======================================================

:: Step 1: Create the Virtual Environment
echo [1/4] 🐍 Creating Python Virtual Environment (venv)...
python -m venv venv
if %errorlevel% neq 0 (
    echo ❌ Failed to create virtual environment. Is Python installed?
    pause
    exit /b
)

:: Step 2: Activate it
echo [2/4] ⚡ Activating the Virtual Environment...
call venv\Scripts\activate

:: Step 3: Install the tech stack
echo [3/4] 📦 Installing Dependencies (FastAPI, Uvicorn, PyGithub)...
python -m pip install --quiet --upgrade pip
pip install fastapi uvicorn PyGithub

:: Step 4: Scaffold the Boilerplate Files
echo [4/4] 📄 Generating Boilerplate Files...
if not exist app.py (
    echo. > app.py
    echo Created app.py
)
if not exist database.json (
    echo { "users": {}, "tests": {} } > database.json
    echo Created database.json vault
)
if not exist .gatekeeperignore (
    echo package-lock.json > .gatekeeperignore
    echo poetry.lock >> .gatekeeperignore
    echo yarn.lock >> .gatekeeperignore
    echo Created .gatekeeperignore
)
pip freeze > requirements.txt

echo =======================================================
echo 🎉 Environment successfully initialized!
echo 🚀 To start the Brain: uvicorn app:app --reload
echo =======================================================
:: Keep the command prompt open and inside the activated venv
cmd /k
