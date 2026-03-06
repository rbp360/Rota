import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

def run_test():
    api_key = os.getenv("GOOGLE_AI_KEY")
    if not api_key:
        print("FAIL: No API KEY")
        return
    
    genai.configure(api_key=api_key)
    print(f"Testing with: gemini-2.0-flash")
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content("Hello")
        print(f"SUCCESS: {response.text}")
    except Exception as e:
        print(f"FAIL: {e}")

if __name__ == "__main__":
    run_test()
