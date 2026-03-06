import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

def test_google():
    api_key = os.getenv("GOOGLE_AI_KEY")
    if not api_key:
        return "FAIL: No GOOGLE_AI_KEY found"
    
    genai.configure(api_key=api_key)
    log = []
    try:
        log.append("Available models:")
        for m in genai.list_models():
            log.append(f" - {m.name}")
            
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content("Say 'Gemini Pro is working!'")
        log.append(f"SUCCESS: {response.text}")
    except Exception as e:
        log.append(f"FAIL: Google AI error: {e}")
    return "\n".join(log)

if __name__ == "__main__":
    res = test_google()
    with open("models_detailed.log", "w") as f:
        f.write(res)
    print("Log written")
