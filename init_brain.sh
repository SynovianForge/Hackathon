#!/bin/bash
echo "======================================================="
echo "🧠 Pop Quiz Gatekeeper: Dev 1 Environment Setup"
echo "======================================================="

# Step 1: Create the Virtual Environment
echo "[1/4] 🐍 Creating Python Virtual Environment (venv)..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "❌ Failed to create virtual environment. Is Python installed?"
    exit 1
fi

# Step 2: Activate it
echo "[2/4] ⚡ Activating the Virtual Environment..."
source venv/bin/activate

# Step 3: Install the tech stack
echo "[3/4] 📦 Installing Dependencies (FastAPI, Uvicorn, PyGithub)..."
python -m pip install --quiet --upgrade pip
pip install fastapi uvicorn PyGithub

# Step 4: Scaffold the Boilerplate Files
echo "[4/4] 📄 Generating Boilerplate Files..."
if [ ! -f "app.py" ]; then
    touch app.py
    echo "Created app.py"
fi
if [ ! -f "database.json" ]; then
    echo '{ "users": {}, "tests": {} }' > database.json
    echo "Created database.json vault"
fi
if [ ! -f ".gatekeeperignore" ]; then
    printf 'package-lock.json\npoetry.lock\nyarn.lock\n' > .gatekeeperignore
    echo "Created .gatekeeperignore"
fi
pip freeze > requirements.txt

echo "======================================================="
echo "🎉 Environment successfully initialized!"
echo "🚀 To start the Brain: uvicorn app:app --reload"
echo "======================================================="
# Keep the shell open with the venv active
exec $SHELL
