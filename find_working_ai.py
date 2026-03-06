import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

def find_working_model():
    key = os.getenv("GOOGLE_AI_KEY")
    if not key:
        print("FAIL: No API KEY")
        return
    
    genai.configure(api_key=key)
    
    # Try these in order
    test_models = [
        'gemini-1.5-flash',
        'gemini-1.5-flash-latest',
        'gemini-1.5-pro',
        'gemini-pro',
        'gemini-1.0-pro'
    ]
    
    for m_name in test_models:
        print(f"Testing: {m_name}...")
        try:
            model = genai.GenerativeModel(m_name)
            response = model.generate_content("Hi")
            print(f"  SUCCESS! {m_name} works.")
            return m_name
        except Exception as e:
            print(f"  FAILED {m_name}: {str(e)[:100]}...")
            
    return None

if __name__ == "__main__":
    found = find_working_model()
    if found:
        print(f"\nFINAL_WINNER: {found}")
    else:
        print("\nNo models worked. Check your AI Studio project quota settings.")
