# Copypasta Hunter

> *You wrote it. You own it. Prove it.*

Copypasta Hunter intercepts git pushes and PR openings, forcing developers to prove they understand their own code changes before anything reaches the repository. No understanding, no merge.

---

## How It Works

Three components, one brain:

**1. VS Code Extension — The Fast Lane**
Installs a `pre-push` git hook. The moment a developer pushes, a 60-second interrogation room opens inside VS Code. An AI generates a hyper-specific question about their exact diff. No copy-paste. No switching windows. Wrong answer or time out — push blocked.

**2. Python Brain — The Command Center**
FastAPI backend that handles all logic: trust level tracking, AI question generation (Gemini), AI answer grading, and the quiz vault. Developers who consistently pass get a higher trust score and get quizzed less often.

**3. GitHub Bot — The Backstop**
Catches anyone who bypasses VS Code entirely. When a PR opens with an unverified commit, the bot drops a magic link comment on the PR. The link opens a standalone web interrogation room. Pass the quiz — commit status flips to green. Fail — PR stays blocked.

---

## Setup

**Requirements:** Python 3.10+, Node.js 20+

**1. Clone and install dependencies**
```bash
git clone https://github.com/SynovianForge/Hackathon.git
cd Hackathon
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
npm install
cd frontend && npm install && cd ..
```

**2. Configure environment**

Create a `.env` file in the root:
```
GEMINI_API_KEY=your_key_here
FRONTEND_URL=http://localhost:3001
PYTHON_API_URL=http://localhost:8000
PORT=3000
```

**3. Launch everything**

Windows:
```bash
run_brain.bat
```

Mac:
```bash
chmod +x run_brain.sh && ./run_brain.sh
```

This starts all three servers — Brain on `8000`, Bot on `3000`, Web UI on `3001`.

**4. Install the VS Code extension**

In VS Code: `Ctrl+Shift+P` → `Install from VSIX` → select `extension/gatekeeper-0.0.1.vsix`

---

## Demo

*Video coming soon.*

---

## Built With

- FastAPI + Google Gemini
- Probot (GitHub App)
- Next.js + Tailwind CSS
- TypeScript (VS Code Extension API)
