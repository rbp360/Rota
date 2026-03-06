import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

def run():
    key = os.getenv("GOOGLE_AI_KEY")
    print(f"Key starts with: {key[:8]}...")
    genai.configure(api_key=key)
    
    # Let's try gemini-2.0-flash
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content("Hello, are you working with the new key?")
        print(f"RESULT: {response.text}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    run()
