from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
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

    # 1b. Already verified by the VS Code extension? Don't double-interrogate.
    already_verified = any(
        t.get("commit_hash") == payload.commit_hash and t.get("status") == "PASS"
        for t in db["tests"].values()
    )
    if already_verified:
        return {
            "action": "PASS",
            "reason": "ALREADY_VERIFIED",
            "message": "Commit verified by the VS Code extension. You're good."
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
    
    # We lock the REFERENCE ANSWER in the vault
    db["tests"][new_quiz_id] = {
        "commit_hash": payload.commit_hash,
        "question": ai_quiz_data.get("question", "What does this code do?"),
        "reference_answer": ai_quiz_data.get("reference_answer", "auto-pass"),
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
    # Pull the hidden reference answer from the vault
    reference_answer = test_record.get("reference_answer", "")

    
    # Call Bot 2 (The AI Judge) - Removed poisoned_variable
    ai_evaluation = evaluate_answer(reference_answer, payload.user_answer)
    
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


@app.get("/api/quiz/{quiz_id}")
async def get_quiz(quiz_id: str):
    """
    Returns the question and metadata for a quiz by ID.
    Used by the web interrogation room (magic link flow).
    """
    db = load_db()
    if quiz_id not in db["tests"]:
        raise HTTPException(status_code=404, detail="Quiz not found.")
    record = db["tests"][quiz_id]
    return {
        "quiz_id": quiz_id,
        "question": record.get("question", "What does this code change do?"),
        "user_id": record.get("user_id", "anonymous"),
        "status": record.get("status", "PENDING"),
    }


QUIZ_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>GateKeeper — Interrogation Room</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      background: #1e1e2e;
      color: #cdd6f4;
      padding: 32px;
      min-height: 100vh;
      user-select: none;
      -webkit-user-select: none;
    }
    textarea { user-select: text; -webkit-user-select: text; }

    .header { display: flex; align-items: center; gap: 12px; margin-bottom: 24px; }
    .header h1 { font-size: 22px; font-weight: 700; color: #cba6f7; }
    .badge {
      background: #f38ba8; color: #1e1e2e;
      font-size: 11px; font-weight: 700;
      padding: 3px 8px; border-radius: 99px; letter-spacing: 0.5px;
    }
    .badge-web { background: #89b4fa; }

    .timer-row { display: flex; align-items: center; gap: 10px; margin-bottom: 20px; }
    .timer-label { font-size: 13px; color: #6c7086; white-space: nowrap; }
    #timer-display {
      font-size: 20px; font-weight: 800; color: #a6e3a1;
      font-variant-numeric: tabular-nums; min-width: 44px;
    }
    #timer-display.warning { color: #fab387; }
    #timer-display.danger  { color: #f38ba8; animation: pulse 0.5s infinite alternate; }
    @keyframes pulse { from { opacity: 1; } to { opacity: 0.5; } }
    .timer-bar-bg { flex: 1; height: 6px; background: #45475a; border-radius: 99px; overflow: hidden; }
    #timer-bar { height: 100%; background: #a6e3a1; border-radius: 99px; width: 100%; transition: width 1s linear, background 0.5s; }

    .card { background: #313244; border-radius: 12px; padding: 20px 24px; margin-bottom: 20px; border: 1px solid #45475a; }
    .card-label { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: #6c7086; margin-bottom: 10px; }
    .question-text { font-size: 16px; line-height: 1.6; color: #cdd6f4; }

    textarea {
      width: 100%; background: #1e1e2e; border: 1px solid #45475a;
      border-radius: 8px; color: #cdd6f4; font-size: 14px;
      padding: 14px; resize: vertical; min-height: 100px;
      outline: none; font-family: inherit; transition: border-color 0.2s;
    }
    textarea:focus { border-color: #cba6f7; }

    .actions { display: flex; gap: 12px; margin-top: 20px; }
    button { padding: 10px 24px; border-radius: 8px; border: none; font-size: 14px; font-weight: 600; cursor: pointer; transition: opacity 0.2s; }
    button:hover { opacity: 0.85; }
    button:disabled { opacity: 0.4; cursor: not-allowed; }
    .btn-submit { background: #cba6f7; color: #1e1e2e; flex: 1; }
    .btn-skip   { background: #45475a; color: #cdd6f4; }
    .hint { font-size: 12px; color: #f38ba8; margin-top: 10px; }
    #empty-warning { display: none; color: #fab387; font-size: 12px; margin-top: 6px; }

    #loading-state {
      display: flex; align-items: center; justify-content: center;
      min-height: 60vh; flex-direction: column; gap: 16px;
    }
    .spinner {
      width: 40px; height: 40px;
      border: 4px solid #45475a; border-top-color: #cba6f7;
      border-radius: 50%; animation: spin 0.8s linear infinite;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
    #loading-text { color: #6c7086; font-size: 14px; }

    #result-state, #error-state {
      display: none; align-items: center; justify-content: center; min-height: 60vh;
    }
    .result-card, .error-card {
      background: #313244; border-radius: 16px; padding: 40px 48px;
      text-align: center; border: 1px solid #45475a; max-width: 520px; width: 100%;
    }
    .result-card h2, .error-card h2 { font-size: 26px; margin-bottom: 16px; }
    .result-card .explanation { font-size: 15px; line-height: 1.6; color: #bac2de; margin-bottom: 16px; }
    .result-card .trust { font-size: 13px; color: #6c7086; margin-bottom: 10px; }
    .result-card .note, .error-card .note { font-size: 12px; color: #45475a; }
    .result-pass h2 { color: #a6e3a1; }
    .result-fail h2 { color: #f38ba8; }
    .error-card { border-color: #f38ba8; }
    .error-card h2 { color: #f38ba8; }
    .error-card p { color: #bac2de; font-size: 14px; line-height: 1.6; }
  </style>
</head>
<body>

  <div id="loading-state">
    <div class="spinner"></div>
    <p id="loading-text">Loading your interrogation...</p>
  </div>

  <div id="error-state">
    <div class="error-card">
      <h2>🚫 Access Error</h2>
      <p id="error-text"></p>
    </div>
  </div>

  <div id="quiz-state" style="display:none">
    <div class="header">
      <h1>🔒 GateKeeper</h1>
      <span class="badge">PR CHECK</span>
      <span class="badge badge-web">WEB INTERROGATION</span>
    </div>

    <div class="timer-row">
      <span class="timer-label">Time remaining:</span>
      <span id="timer-display">60s</span>
      <div class="timer-bar-bg"><div id="timer-bar"></div></div>
    </div>

    <div class="card">
      <div class="card-label">❓ Quiz Question</div>
      <p class="question-text" id="question-text"></p>
    </div>

    <div class="card">
      <div class="card-label">✏️ Your Answer</div>
      <textarea id="answer" placeholder="Type your answer here..." autocomplete="off" spellcheck="false"></textarea>
      <p id="empty-warning">⚠️ Please write an answer before submitting.</p>
      <p class="hint">⚠️ Copy-paste disabled. Switching windows will auto-fail the quiz.</p>
    </div>

    <div class="actions">
      <button class="btn-submit" id="btn-submit" onclick="submitAnswer()">Submit Answer ✅</button>
      <button class="btn-skip" onclick="doSubmit('')">Skip (Block PR) ❌</button>
    </div>
  </div>

  <div id="result-state"></div>

  <script>
    let quiz_id = null, user_id = null;
    let submitted = false, quizActive = false;
    let remaining = 60, timerInterval = null;
    const TOTAL = 60;

    const params = new URLSearchParams(window.location.search);
    quiz_id = params.get('quiz_id');

    window.addEventListener('load', () => {
      if (!quiz_id) { showError('Invalid magic link — no quiz_id provided.'); return; }

      fetch('/api/quiz/' + encodeURIComponent(quiz_id))
        .then(r => r.ok ? r.json() : r.json().then(d => { throw new Error(d.detail || r.status); }))
        .then(data => {
          user_id = data.user_id;
          if (data.status !== 'PENDING') {
            showError('This quiz has already been used (' + data.status + '). Magic links are one-time only.');
            return;
          }
          startQuiz(data.question);
        })
        .catch(err => showError('Could not load quiz: ' + err.message));
    });

    function startQuiz(question) {
      document.getElementById('question-text').textContent = question;
      document.getElementById('loading-state').style.display = 'none';
      document.getElementById('quiz-state').style.display = 'block';
      quizActive = true;
      const display = document.getElementById('timer-display');
      const bar = document.getElementById('timer-bar');
      timerInterval = setInterval(() => {
        if (submitted) return;
        remaining = Math.max(0, remaining - 1);
        display.textContent = remaining + 's';
        bar.style.width = (remaining / TOTAL * 100) + '%';
        if (remaining <= 10) { display.className = 'danger'; bar.style.background = '#f38ba8'; }
        else if (remaining <= 20) { display.className = 'warning'; bar.style.background = '#fab387'; }
        if (remaining <= 0) doSubmit('');
      }, 1000);
      document.getElementById('answer').focus();
    }

    function submitAnswer() {
      const answer = document.getElementById('answer').value.trim();
      if (!answer) { document.getElementById('empty-warning').style.display = 'block'; return; }
      document.getElementById('empty-warning').style.display = 'none';
      doSubmit(answer);
    }

    function doSubmit(answer) {
      if (submitted) return;
      submitted = true; quizActive = false;
      clearInterval(timerInterval);
      document.getElementById('btn-submit').disabled = true;
      document.getElementById('quiz-state').style.display = 'none';
      document.getElementById('loading-state').style.display = 'flex';
      document.getElementById('loading-text').textContent = 'Grading your answer...';

      fetch('/api/submit-answer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: user_id || 'anonymous', quiz_id: quiz_id, user_answer: answer })
      })
        .then(r => r.json())
        .then(d => showResult(d.status === 'PASS', d.explanation, d.new_trust_level))
        .catch(() => showResult(false, 'Server error during grading. Contact a senior engineer.', null));
    }

    function showResult(passed, explanation, trust) {
      document.getElementById('loading-state').style.display = 'none';
      const el = document.getElementById('result-state');
      el.style.cssText = 'display:flex; align-items:center; justify-content:center; min-height:60vh;';
      const trustLine = trust !== null && trust !== undefined ? '<p class="trust">New trust level: ' + trust + ' / 100</p>' : '';
      const note = passed
        ? '<p class="note">Your PR has been unlocked. You may close this tab.</p>'
        : '<p class="note">Your PR remains blocked. Reply @Gatekeeper-Bot appeal for manual review.</p>';
      el.innerHTML =
        '<div class="result-card ' + (passed ? 'result-pass' : 'result-fail') + '">' +
        '<h2>' + (passed ? '✅ Access Granted' : '❌ Access Denied') + '</h2>' +
        '<p class="explanation">' + esc(explanation || (passed ? 'Correct.' : 'Incorrect.')) + '</p>' +
        trustLine + note + '</div>';
    }

    function showError(msg) {
      document.getElementById('loading-state').style.display = 'none';
      const el = document.getElementById('error-state');
      el.style.cssText = 'display:flex; align-items:center; justify-content:center; min-height:60vh;';
      document.getElementById('error-text').textContent = msg;
    }

    function esc(t) {
      return (t || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    }

    // Anti-cheat
    document.addEventListener('copy',        e => e.preventDefault());
    document.addEventListener('cut',         e => e.preventDefault());
    document.addEventListener('paste',       e => e.preventDefault());
    document.addEventListener('contextmenu', e => e.preventDefault());
    document.addEventListener('dragover',    e => e.preventDefault());
    document.addEventListener('drop',        e => e.preventDefault());

    window.addEventListener('blur', () => { if (quizActive) doSubmit(''); });
    document.addEventListener('visibilitychange', () => { if (document.hidden && quizActive) doSubmit(''); });

    document.addEventListener('keydown', e => {
      const blocked = e.key === 'F12'
        || (e.ctrlKey  && e.shiftKey && ['I','J','C'].includes(e.key))
        || (e.metaKey  && e.shiftKey && ['I','J','C'].includes(e.key))
        || (e.ctrlKey  && e.key === 'u')
        || (e.metaKey  && e.key === 'u');
      if (blocked) e.preventDefault();
    });
  </script>
</body>
</html>"""


@app.get("/quiz", response_class=HTMLResponse)
async def quiz_page():
    """Standalone web interrogation room — opened via the magic link from a PR comment."""
    return HTMLResponse(content=QUIZ_HTML)