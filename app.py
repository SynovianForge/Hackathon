from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import json
import os
import uuid
import random

# Import our new AI Micro-Agent architecture
from ai_engine import generate_quiz, evaluate_answer

# ==========================================
# 1. API Configuration & Setup
# ==========================================
app = FastAPI(title="Gatekeeper Brain API", version="1.0")
DB_FILE = "database.json"

# ==========================================
# 2. Database Helper Functions
# ==========================================
def load_db():
    if not os.path.exists(DB_FILE):
        return {"users": {}, "tests": {}}
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ==========================================
# 3. Data Models (Pydantic)
# These ensure the Frontend sends the exact payload we expect
# ==========================================
class FileDiff(BaseModel):
    filename: str
    diff: str
    context: Optional[str] = ""

class CheckPushRequest(BaseModel):
    user_id: str
    commit_hash: str
    total_diff_size: int
    files: List[FileDiff]

class SubmitAnswerRequest(BaseModel):
    user_id: str
    quiz_id: str
    user_answer: str

# ==========================================
# 4. Core Endpoints
# ==========================================

@app.post("/api/check-push")
async def check_push(payload: CheckPushRequest):
    """
    Endpoint 1: Fired when a developer attempts to push code.
    Evaluates trust level and either passes them or generates a quiz.
    """
    db = load_db()
    
    # 1. DevEx Fallback: Is the diff too massive?
    if payload.total_diff_size > 5000:
        return {
            "action": "PASS",
            "reason": "DIFF_TOO_LARGE",
            "message": "Massive push detected. Bypassing AI to save limits."
        }

    # 2. Check Trust Level (Probabilistic)
    user = db["users"].get(payload.user_id, {"trust_level": 50, "test_history": []})
    
    # Roll a 100-sided die. 
    # If trust is 80, they have an 80% chance to roll under it (PASS), 
    # and a 20% chance to roll over it (INTERROGATE).
    roll = random.randint(1, 100)
    
    if roll <= user["trust_level"]:
        return {
            "action": "PASS",
            "reason": "TRUST_LEVEL_PASSED",
            "message": f"Push allowed. You beat the {100 - user['trust_level']}% interrogation odds!"
        }

    # 3. INTERROGATION TIME (LIVE AI LOGIC)
    # Combine the diffs from the payload to create the context for the AI
    diff_context = "\n".join([f"File: {f.filename}\n{f.diff}" for f in payload.files])
    
    # Call Bot 1 (The Interrogator) and Bot 3 (The Steganographer)
    ai_quiz_data = generate_quiz(diff_context, payload.commit_hash)
    
    new_quiz_id = f"quiz_{uuid.uuid4().hex[:6]}"
    
    # We lock the REFERENCE ANSWER and TRAP VARIABLE in the vault (database.json)
    db["tests"][new_quiz_id] = {
        "commit_hash": payload.commit_hash,
        "reference_answer": ai_quiz_data.get("reference_answer", "auto-pass"),
        "poisoned_variable": ai_quiz_data.get("poisoned_variable"),
        "status": "PENDING",
        "user_id": payload.user_id
    }
    
    # Ensure user exists in DB and save
    db["users"][payload.user_id] = user
    save_db(db)

    # Return ONLY the generated question to the frontend
    return {
        "action": "INTERROGATE",
        "quiz_id": new_quiz_id,
        "question": ai_quiz_data.get("question", "API Error: What does this code do?"),
        "timer_seconds": 60
    }


@app.post("/api/submit-answer")
async def submit_answer(payload: SubmitAnswerRequest):
    """
    Endpoint 2: Receives the user's answer and grades it using the AI Judge.
    """
    db = load_db()
    
    # Safety check
    if payload.quiz_id not in db["tests"]:
        raise HTTPException(status_code=404, detail="Quiz ID not found in vault.")
        
    test_record = db["tests"][payload.quiz_id]
    
    # Ensure the user dictionary has the history list initialized
    user_record = db["users"].get(payload.user_id, {"trust_level": 50, "test_history": []})
    if "test_history" not in user_record:
        user_record["test_history"] = []

    # 4. GRADING TIME (LIVE AI LOGIC)
    # Pull the hidden reference answer and trap from the vault
    reference_answer = test_record.get("reference_answer", "")
    poisoned_variable = test_record.get("poisoned_variable")
    
    # Call Bot 2 (The AI Judge)
    ai_evaluation = evaluate_answer(reference_answer, payload.user_answer, poisoned_variable)
    
    status = ai_evaluation.get("status", "FAIL")
    explanation = ai_evaluation.get("explanation", "AI Evaluation Failed.")

    # Adjust trust score based on the AI's binary ruling
    if status == "PASS":
        # Bump score by +1, max 100
        user_record["trust_level"] = min(100, user_record["trust_level"] + 1) 
    else:
        # Dock score by -10, min 0
        user_record["trust_level"] = max(0, user_record["trust_level"] - 10) 

    # Add this quiz to their permanent record
    user_record["test_history"].append(payload.quiz_id)

    # Update Vault
    test_record["status"] = status
    db["tests"][payload.quiz_id] = test_record
    db["users"][payload.user_id] = user_record
    save_db(db)

    return {
        "status": status,
        "explanation": explanation,
        "new_trust_level": user_record["trust_level"]
    }