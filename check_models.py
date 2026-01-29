import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GOOGLE_AI_KEY")
if not API_KEY:
    print("No GOOGLE_AI_KEY found.")
else:
    genai.configure(api_key=API_KEY)
    print("Available models supporting generateContent:")
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(m.name)
    except Exception as e:
        print(f"Error listing models: {e}")
