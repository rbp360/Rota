import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

def test_google():
    api_key = os.getenv("GOOGLE_AI_KEY")
    if not api_key:
        return "FAIL: No GOOGLE_AI_KEY found"
    
    genai.configure(api_key=api_key)
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content("Say 'Gemini 2.0 is working!'")
        return f"SUCCESS: {response.text}"
    except Exception as e:
        return f"FAIL: Google AI error: {e}"

def test_imports():
    try:
        import openai
        import crewai
        import langchain
        return "SUCCESS: All imports (OpenAI, CrewAI, Langchain) working"
    except Exception as e:
        return f"FAIL: Import error: {e}"

if __name__ == "__main__":
    with open("ai_smoke_test.log", "w") as f:
        f.write("--- AI Smoke Test ---\n")
        f.write(f"Imports: {test_imports()}\n")
        f.write(f"Google AI: {test_google()}\n")
    print("Done")
