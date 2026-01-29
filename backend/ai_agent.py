import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

# Configure Google AI Studio API Key
API_KEY = os.getenv("GOOGLE_AI_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

class RotaAI:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-flash-latest')

    def suggest_cover(self, absent_staff, day, periods, available_staff_profiles):
        if not os.getenv("GOOGLE_AI_KEY"):
            return "Error: GOOGLE_AI_KEY not found in environment."

        prompt = f"""
        Internal School Cover System:
        
        Teacher Absent: {absent_staff}
        Day: {day}
        Periods Required: {periods}
        
        Available Staff and their specialty/priority:
        {available_staff_profiles}
        
        Goal: Pick the best cover for each period.
        Constraints:
        1. Claire and dedicated cover staff (is_priority) are first port of call.
        2. Specialist teachers/Non-form teachers (is_specialist: True, e.g., Billy, Jinny) should be considered next as they don't have their own forms.
        3. Match specialties (e.g., Music for Music) where possible.
        4. Explain WHY you chose them.
        
        Output format: Concise text explaining the selection.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"AI Generation Error: {e}")
            return f"Error: Failed to generate AI content. {str(e)}"

    def generate_report(self, query, data_context):
        if not os.getenv("GOOGLE_AI_KEY"):
            return "Error: GOOGLE_AI_KEY not found in environment."

        prompt = f"""
        Internal School Rota AI Report Generator:
        
        You are an assistant for a school cover system. You have access to the following historical data:
        
        {data_context}
        
        User Query: {query}
        
        Goal: Provide a concise and accurate report based on the data provided. 
        If a user asks for counts (e.g., "how many times..."), be specific.
        If the data doesn't contain information to answer the query, say so politely.
        
        Output format: Concise, professional text or a small table if appropriate.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"AI Report Generation Error: {e}")
            return f"Error: Failed to generate report. {str(e)}"
