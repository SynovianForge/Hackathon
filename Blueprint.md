# Pop Quiz Code Gatekeeper

---

## 🧠 Component 1: The Brain (Python Backend API)

This is the central command center where all the actual thinking happens. It's a lightweight API (likely FastAPI or Flask) that handles the heavy lifting so your frontends stay fast.

- **Trust Level Manager:** Tracks user scores to determine if they get quizzed or if they get a free pass.
- **The Interrogator (AI Generator):** Fetches the git diff (`file.patch`) and asks an LLM to generate an "Un-Googlable Prompt". This is a 40-word code snippet with a subtle bug.
- **The AI Judge:** Takes the user's answer and evaluates it for actual comprehension. It returns a binary `PASS` or `FAIL` with a one-sentence explanation. It also docks points if it detects standard AI "Robo-Speak".

---

## ⚡ Component 2: The Fast Lane (VS Code Extension)

This is our primary trap, designed to feel like a native part of the developer workflow.

- **The Engine:** Written in TypeScript/JavaScript running on Node.js. It intercepts the local `git push` command.
- **The Interrogation Room (Webview):** A secure iframe inside the editor that displays the AI-generated question.
- **Anti-Cheat Mechanics:** Uses JavaScript to disable clipboard copying (`onCopy`) and enforces a high-pressure 60-to-90 second micro-timer.
- **The Handshake:** If the user passes, the extension silently tells the Python Backend to tag that specific Git commit hash as "Verified" in the database.

---

## 🧱 Component 3: The Unforgiving Backstop (GitHub Bot & Web App)

This catches anyone trying to bypass the VS Code extension by using the terminal or another IDE.

- **The Tripwire:** A GitHub Action triggers whenever a Pull Request is opened.
- **The Database Check:** The bot checks the backend database to see if the incoming commit hash is marked as "Verified".
- **The Fallback (Magic Link):** If the commit is unverified, the bot posts a comment on the PR: `🚨 Gatekeeper Check Required.`
- **The Zero-Friction Web App:** The PR comment contains a one-time, cryptographically signed "Magic Link". This link drops the user into a standalone web version of the Interrogation Room, completely eliminating the need for a login screen.

---

## Future Improvements

- **The Steganography Trap:** Secretly swaps out a variable name in the prompt (e.g., `user_id` to `usr_auth_token_99x`) to catch interns using AI vision tools.
- **Webcam Checking:** Integrates with the browser's MediaStream API during the quiz (Component 2) to capture a feed of the user. The AI Judge processes the feed to ensure the developer is present and to detect external screens, phones, or other people trying to help. If the AI detects suspicious activity, it automatically fails the quiz.

---

## The 50-Hour Battle Plan

### 👔 The Pitch Master (The Non-Coder)

**The Mission:** Win the money.

**Action Items:** They should not be fetching you coffee; they need to be writing the story. Have them immediately start building the slide deck targeting the sponsors. They need to craft the pitch specifically explaining how your "AI Judge" makes this the perfect tool for Noverse (AI grading), and how intercepting the `git push` makes it an ultimate workflow optimization for LintLabs. They should design the demo flow using mockups before the code is even finished.

---

### 💻 Dev 1: The Brain Surgeon (Component 1)

**The Mission:** Build the Python Backend API.

**Action Items:** This dev spins up the FastAPI/Flask server. Their entire 50 hours is dedicated to the LLM logic. They need to write the prompts for the "Interrogator" to generate the 40-word code snippets, and they need to build the "AI Judge" that returns a binary `PASS` or `FAIL`.

> **Mocking is key:** Tell them to hardcode a fake JSON response first so the other devs can start building against it immediately.

---

### 💻 Dev 2: The Bouncer (Component 3)

**The Mission:** The GitHub Bot & The Tripwire.

**Action Items:** This dev lives in YAML and GitHub API docs. They are setting up the GitHub Action that triggers when a Pull Request opens. They need to connect GitHub to Dev 1's Python API to drop the `🚨 Gatekeeper Check Required` comment into the PR.

---

### 💻 Dev 3: The UI Wizard (Component 2)

**The Mission:** The VS Code Extension / The Interrogation Room.

**Action Items:** This is the highest risk, highest reward job. This dev is writing TypeScript/Node.js to intercept the local `git push`. They have to get the Webview iframe rendering, lock down the clipboard, and build the panic-inducing 60-second micro-timer.

---

## Edge Cases

### 1. The "Lockfile Bankruptcy" Loophole

**The Problem:** We made a smart call earlier: we decided to send the `file.patch` (the diff) to the AI instead of the whole file to save API tokens. But what happens when an intern runs `npm install` or `poetry update` and commits a change to a `package-lock.json` or `poetry.lock` file? Those files are auto-generated and can easily have 20,000 lines of changes. If your Python script blindly grabs that diff and sends it to the AI, the AI will choke, fail to generate a question, and burn through your API budget in seconds.

**The Fix:** Your Python Brain needs a strict filtration system (like a `.gatekeeperignore` file). Before it sends anything to the AI, it must strip out lockfiles, `.svg` images, minified `.js` files, and any auto-generated code.

---

### 2. The Asynchronous Race Condition

**The Problem:** Let's trace the "Happy Path". The developer pushes via VS Code. They pass the quiz, and the extension tells the Python Backend to tag that commit hash as "Verified". However, the moment that code actually hits GitHub, the GitHub Action tripwire instantly wakes up and checks the database. What if GitHub's servers are faster than your Python backend's database write speed? The GitHub bot will query the DB, see the commit isn't verified yet, and slap the PR with a warning. Two seconds later, the DB updates. Now you have a blocked PR and a highly annoyed developer.

**The Fix:** Add a "wait-and-retry" loop inside the GitHub Action. If the database says "Unverified," the bot should sleep for 5 seconds and check one more time before officially dropping the hammer.

---

### 3. The "Ten-Commit Push" (A DevEx Nightmare)

**The Problem:** Developers don't always push one commit at a time. If an intern works offline for four hours, they might have 12 separate commits stacked up. When they type `git push`, does your extension trap them in the Interrogation Room and force them to answer 12 back-to-back AI quizzes? If so, they will uninstall your extension immediately.

**The Fix:** The extension shouldn't evaluate individual commits. It needs to look at the **aggregate diff** — the total sum of all changes being pushed from the local branch to the remote branch — and just generate one comprehensive question for the entire batch.

---

### 4. The "Linter Nuke" (Whitespace & Formatting)

**The Problem:** A developer installs a code formatter like Prettier or Black for the first time. They hit save, and suddenly every single file gets its indentation changed. The `git diff` will literally be 10,000 lines of changes. If we feed that to the AI, it will try to ask a complex logical question about why we added spaces to line 42.

**The Fix:** Instruct your Git diff parser to ignore whitespace changes (`git diff -w`). If the diff is empty after stripping whitespace, the Gatekeeper silently approves the PR and goes back to sleep.

---

### 5. The "Whoops" Commit (Git Reverts)

**The Problem:** Production goes down. A developer realizes their last commit broke everything. Sweating profusely, they type `git revert HEAD` to instantly undo their changes and push. Right as they are trying to save the company, your Gatekeeper jumps out and says, "Pop Quiz!" They will literally throw their laptop out the window.

**The Fix:** Add a bypass valve for emergencies. Your Python backend needs to read the commit message or branch name. If it detects `Revert "..."` or if the diff is 100% deletions, it grants an automatic pass. We don't interrogate people while the building is on fire.

---

### 6. The "Drunk AI" (Hallucinations & Appeals)

**The Problem:** We are relying on an LLM to act as a judge. Even the best models occasionally hallucinate. What happens when the AI generates a code snippet that makes no logical sense, or the developer provides the 100% correct answer but the AI Judge incorrectly grades it as `FAIL`?

**The Fix:** The **"Appeal to a Human" button**. If the bot fails them, they cannot be permanently locked out of their PR. We must provide a button or command (like replying `@Gatekeeper-Bot appeal`) that bypasses the AI, tags a human Senior Engineer for a manual review, and temporarily pauses the timer.

---

### 7. The "Merge Commit" Madness

**The Problem:** An intern has been working on a feature branch for two weeks. Meanwhile, the senior devs have merged 50 Pull Requests into `main`. The intern runs `git merge main` to catch up. Suddenly, their `git push` includes hundreds of changes that other people wrote. The AI is going to interrogate the intern about complex backend architecture they have never seen before.

**The Fix:** Be surgical with our Git commands. We cannot use standard `git diff`. We must use the **three-dot diff** (e.g., `git diff main...feature_branch`). This specifically isolates only the changes introduced by the current feature branch, ignoring all incoming code from `main`.

---

### 8. The "Global Find-and-Replace" Trap

**The Problem:** A developer uses their IDE to do a global find-and-replace, changing `userID` to `userUUID` across the entire project. This touches 450 files but only changes one word per file. Our AI prompt asks for a "subtle bug" and "applied logic". If we feed this massive, purely cosmetic diff to the AI, it will likely hallucinate a bug that doesn't exist.

**The Fix:** Introduce a **Diff Variance Threshold** in the Python Brain. If the script detects that 100+ files were changed but the Levenshtein distance between the old string and new string is nearly identical across all of them, it flags the PR as a "Refactor" and grants an automated pass.

---

### 9. The "Monorepo" Mayhem (Markdown & YAML)

**The Problem:** Modern companies love monorepos. You might have your Python backend, React frontend, Docker configurations, and documentation all in one giant repository. If a developer fixes a typo in the `README.md` or updates a version number in a `.yaml` file, you are going to force them into a 60-second interrogation about a comma in a Markdown file. You are going to face a mutiny.

**The Fix:** Path-based and extension-based whitelisting. Before the Python Brain wakes up the AI, it checks the file paths of the diff. Configure the Gatekeeper to only trigger on actual source code files (e.g., `.py`, `.js`, `.ts`, `.rs`) located within specific executable directories (like `src/` or `app/`). Everything else gets a free pass.

---

## API Endpoints

### 🛣️ Endpoint 1: The Gatekeeper Check — `POST /api/check-push`

This is fired the millisecond the user attempts to push code. It handles both the Trust Level check and the Question Generation.

**Request Payload (Frontend → Backend):**

```json
{
  "user_id": "github_dave123",
  "commit_hash": "a1b2c3d",
  "total_diff_size": 450,
  "files": [
    {
      "filename": "src/auth/login.ts",
      "diff": "@@ -14,5 +14,5 @@\n- const token = localStorage.getItem('token');\n+ const token = sessionStorage.getItem('token');",
      "context": "function getAuthToken() {\n  // fetch token\n  const token = sessionStorage.getItem('token');\n  return token;\n}"
    }
  ]
}
```

> **Note:** We send `total_diff_size`. If this number is over 5,000, the Backend can instantly issue a `PASS` without even parsing the files to save the AI from crashing.

**Response — Scenario A: High Trust / Fast Track:**

```json
{
  "action": "PASS",
  "reason": "TRUST_LEVEL_HIGH",
  "message": "Push allowed. Trust level at 85%."
}
```

**Response — Scenario B: Low Trust / Interrogation Time:**

```json
{
  "action": "INTERROGATE",
  "quiz_id": "quiz_8829",
  "question": "Why did you switch from localStorage to sessionStorage in the getAuthToken function?",
  "timer_seconds": 60
}
```

---

### 🛣️ Endpoint 2: The Interrogation Room — `POST /api/submit-answer`

If Endpoint 1 returned `INTERROGATE`, the Frontend locks the screen, shows the question, and hits this endpoint when the user submits (or when the timer hits zero).

**Request Payload (Frontend → Backend):**

```json
{
  "user_id": "github_dave123",
  "quiz_id": "quiz_8829",
  "user_answer": "sessionStorage clears when the tab closes, which fixes the session hijack vulnerability we had."
}
```

> **Note:** If the timer runs out, the Frontend should send `"user_answer": ""` so the Backend knows to automatically fail them.

**Response Payload (Backend → Frontend):**

```json
{
  "status": "PASS",
  "explanation": "Correct. You accurately identified the security benefit of session expiration.",
  "new_trust_level": 45
}
```

If `status` is `"FAIL"`, the Frontend blocks the push and shows the explanation. If `"PASS"`, the Frontend drops the lock and lets the push through.

---

## 🧠 The Developer Experience (DevEx) Win

By combining the Trust Check and Question Generation into Endpoint 1, you only need **two API routes total**:

1. Frontend asks: *"Can I push this?"*
2. Backend replies: *"Yes,"* OR *"No, answer this first."*
3. Frontend asks: *"Is this answer right?"*
4. Backend replies: *"Yes,"* OR *"No."*

This is incredibly clean to build and debug.