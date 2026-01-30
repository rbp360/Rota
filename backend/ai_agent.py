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
        
        Available Staff and their specialty/priority/schedule:
        {available_staff_profiles}
        
        Goal: Pick the best cover for each period.
        Constraints:
        1. Claire and dedicated cover staff (is_priority) are first port of call.
        2. Specialist teachers/Non-form teachers (is_specialist: True, e.g., Billy, Jinny) should be considered next as they don't have their own forms.
        3. Match specialties (e.g., Music for Music) where possible.
        4. ANALYSIS OF BUSY TIMES:
           - 'busy_periods' shows their regular timetable (e.g. "Year 4 Lesson"). These are usually hard to move.
           - 'calendar_events' shows Outlook/ICS events (e.g. "Meeting with Head").
           - If no one is 'free', look at these busy activities. If an activity looks like a meeting that could be cancelled or a non-essential task (e.g., "Planning", "Meeting"), you can suggest that person but explicitly mention the meeting title and suggest they cancel/move it.
           - DO NOT suggest pulling someone from "Class Teaching" or "Year X Lesson" unless absolutely desperate.
        5. CRITICAL: Staff with 'can_cover_periods': False (e.g. TAs) CANNOT cover teaching periods (1-8). They can ONLY cover Duties (Morning, Lunch, Break, After School). Do not suggest them for classes.
        6. Explain WHY you chose them, mentioning any meetings they might have to move.
        
        Output format: Concise text explaining the selection per period.
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
