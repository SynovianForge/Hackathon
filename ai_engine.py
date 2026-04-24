from google import genai
from google.genai import types
import json
import os
from dotenv import load_dotenv

# Load the environment variables
load_dotenv()

# Initialize the Gemini client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Enforce JSON output
json_config = types.GenerateContentConfig(response_mime_type="application/json")

# -------------------------------------------------------------------
# 🧠 BOT 1: THE INTERROGATOR
# -------------------------------------------------------------------
def generate_quiz(diff_context: str, commit_hash: str) -> dict:
    """
    Fetches the git diff and uses an LLM to generate Un-Googlable Prompts.
    """
    try:
        system_prompt = f"""
        You are a ruthless Staff Engineer interrogating an intern.
        Review the following code diff:
        {diff_context}

        Generate a hyper-specific, un-googlable prompt about this code.
        Rules:
        1. Keep the prompt under 40 words.
        2. Focus on the WHY, pointing out a subtle bug or applied logic.
        3. Provide the reference answer.

        Output valid JSON with the keys: "question", "reference_answer".
        """

        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=system_prompt,
            config=json_config
        )

        ai_payload = json.loads(response.text)

        return {
            "question": ai_payload["question"],
            "reference_answer": ai_payload["reference_answer"]
        }

    except Exception as e:
        print(f"Interrogator Error: {e}")
        return {
            "question": "API Timeout. What does this code do?",
            "reference_answer": "auto-pass"
        }

# -------------------------------------------------------------------
# ⚖️ BOT 2: THE AI JUDGE
# -------------------------------------------------------------------
def evaluate_answer(reference_answer: str, user_answer: str) -> dict:
    """
    Evaluates user answers for actual comprehension, returning a binary PASS/FAIL.
    """
    try:
        system_prompt = f"""
        You are a strict code evaluator.
        Compare the user's answer to the reference answer to determine code comprehension.

        Reference Answer: {reference_answer}
        User's Answer: {user_answer}

        Rules:
        1. Evaluate for comprehension. Ignore grammar/spelling. Focus on technical accuracy.
        2. Dock points and fail the user if they use "Robo-Speak" (e.g., "As an AI...").
        3. Output valid JSON with the keys: "status" (strictly "PASS" or "FAIL"), and "explanation" (one sentence).
        """

        response = client.models.generate_content(
            model="gemini-3.1-flash-lite-preview",
            contents=system_prompt,
            config=json_config
        )

        result = json.loads(response.text)
        status = "PASS" if "PASS" in result["status"].upper() else "FAIL"

        return {
            "status": status,
            "explanation": result["explanation"]
        }

    except Exception as e:
        print(f"Judge Error: {e}")
        return {
            "status": "PASS",
            "explanation": "API Timeout - Auto-Granted Pass."
        }