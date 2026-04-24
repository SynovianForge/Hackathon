import google.generativeai as genai
import json
import os
from dotenv import load_dotenv

# Load the environment variables from the .env file BEFORE configuring genai
load_dotenv() 

# Initialize the Gemini API
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# We enforce JSON output at the API level to prevent parsing crashes
json_config = {"response_mime_type": "application/json"}

# -------------------------------------------------------------------
# 🦹 BOT 3: THE STEGANOGRAPHER (Anti-Cheat Forger)
# -------------------------------------------------------------------
def apply_steganography_trap(diff_text: str) -> dict:
    """
    Intelligently weaves a poisoned variable into the code syntax
    so perfectly that it becomes entirely undetectable to the human eye.
    """
    try:
        # Initialize Bot 3 Model (Fast and intelligent forger)
        forger_model = genai.GenerativeModel("gemini-3.1-flash-lite-preview")
        
        system_prompt = f"""
        You are a covert Steganographer AI.
        Review the following code diff:
        {diff_text}
        
        Your objective:
        1. Find a common variable name in this code (e.g., user_data, config, id).
        2. Intelligently and naturally rename it to 'usr_auth_token_99x' without breaking the logical flow of the snippet.
        3. Return the modified code and the name of the original variable you replaced.
        
        Output valid JSON with the keys: "poisoned_diff", "original_variable", and "poisoned_variable" (which must be 'usr_auth_token_99x').
        """
        
        response = forger_model.generate_content(
            system_prompt,
            generation_config=json_config
        )
        
        return json.loads(response.text)
        
    except Exception as e:
        # The DevEx Fallback: Return the original diff if the API hiccups
        print(f"Forger Error: {e}")
        return {
            "poisoned_diff": diff_text, 
            "original_variable": None,
            "poisoned_variable": None
        }

# -------------------------------------------------------------------
# 🧠 BOT 1: THE INTERROGATOR
# -------------------------------------------------------------------
def generate_quiz(diff_context: str, commit_hash: str) -> dict:
    """
    Fetches the git diff and uses an LLM to generate Un-Googlable Prompts.
    """
    try:
        # Pass the code through Bot 3 first to set the trap
        trap_data = apply_steganography_trap(diff_context)
        poisoned_diff = trap_data.get("poisoned_diff", diff_context)
        poisoned_var = trap_data.get("poisoned_variable")
        
        # Initialize Bot 1 Model (The Heavy Lifter for complex reasoning)
        interrogator_model = genai.GenerativeModel("gemini-3.1-pro-preview")
        
        system_prompt = f"""
        You are a ruthless Staff Engineer interrogating an intern. 
        Review the following code diff:
        {poisoned_diff}
        
        Generate a hyper-specific, un-googlable prompt about this code. 
        Rules:
        1. Keep the prompt under 40 words.
        2. Focus on the WHY, pointing out a subtle bug or applied logic. 
        3. Provide the reference answer.
        
        Output valid JSON with the keys: "question", "reference_answer".
        """
        
        response = interrogator_model.generate_content(
            system_prompt, 
            generation_config=json_config
        )
        
        ai_payload = json.loads(response.text)
        
        return {
            "question": ai_payload["question"],
            "reference_answer": ai_payload["reference_answer"],
            "poisoned_variable": poisoned_var
        }
        
    except Exception as e:
        # DevEx Fallback
        print(f"Interrogator Error: {e}")
        return {
            "question": "API Timeout. What does this code do?",
            "reference_answer": "auto-pass",
            "poisoned_variable": None
        }

# -------------------------------------------------------------------
# ⚖️ BOT 2: THE AI JUDGE
# -------------------------------------------------------------------
def evaluate_answer(reference_answer: str, user_answer: str, poisoned_variable: str) -> dict:
    """
    Evaluates user answers for actual comprehension, returning a binary PASS/FAIL.
    """
    try:
        # Check if the user tripped Bot 3's trap
        if poisoned_variable and poisoned_variable in user_answer:
            return {
                "status": "FAIL",
                "explanation": f"Automated AI Cheat Detected. You referenced a fake variable ({poisoned_variable}) that was injected to catch OCR vision tools."
            }
            
        # Initialize Bot 2 Model (Ultra-fast grader)
        judge_model = genai.GenerativeModel("gemini-3.1-flash-lite-preview")
        
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
        
        response = judge_model.generate_content(
            system_prompt, 
            generation_config=json_config
        )
        
        result = json.loads(response.text)
        
        # Enforce strict binary output
        status = "PASS" if "PASS" in result["status"].upper() else "FAIL"
        
        return {
            "status": status,
            "explanation": result["explanation"]
        }
        
    except Exception as e:
        # DevEx Fallback
        print(f"Judge Error: {e}")
        return {
            "status": "PASS",
            "explanation": "API Timeout - Auto-Granted Pass."
        }