import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
import base64
import re

# Global variable for the firestore client
_db = None

def get_db():
    global _db
    if _db is not None:
        return _db
        
    if not firebase_admin._apps:
        service_account_info = os.getenv("FIREBASE_SERVICE_ACCOUNT")
        
        if service_account_info:
            # 1. CLEANING: Remove ALL whitespace/newlines from the raw input
            # Vercel often adds spaces or line breaks when importing .env files
            raw_input = "".join(service_account_info.split())
            
            # Remove any wrapping quotes
            if raw_input.startswith('"') and raw_input.endswith('"'):
                raw_input = raw_input[1:-1]
            if raw_input.startswith("'") and raw_input.endswith("'"):
                raw_input = raw_input[1:-1]

            detected_type = "json" if raw_input.startswith('{') else "b64"
            
            try:
                if detected_type == "b64":
                    # Step 1: Decode Base64 (ignoring any remaining whitespace)
                    decoded_bytes = base64.b64decode(raw_input)
                    info_str = decoded_bytes.decode('utf-8')
                else:
                    info_str = raw_input

                # Step 2: REPAIR THE JSON STRING
                # This fixes the "Invalid \escape" error specifically.
                # It replaces literal backslashes with doubled backslashes, 
                # but only where they aren't part of a valid escape sequence.
                def clean_json_string(s):
                    # Step A: Handle literal newlines that should be \n
                    s = s.replace('\n', '\\n').replace('\r', '')
                    # Step B: Fix double escaped backslashes common in Vercel
                    s = s.replace('\\\\', '\\')
                    # Step C: Re-escape the private key specifically (the most fragile part)
                    # We look for the private_key start and ensure newlines are \n
                    if '"private_key":' in s:
                        parts = s.split('"private_key":')
                        # The start of the key string
                        key_part = parts[1].split('"', 2)
                        if len(key_part) >= 3:
                            # Clean the inner key content
                            cleaned_key = key_part[1].replace('\\n', '\n').replace('\n', '\\n')
                            parts[1] = '"' + cleaned_key + '"' + key_part[2]
                            s = '"private_key":'.join(parts)
                    return s

                try:
                    info = json.loads(info_str)
                except:
                    # If raw fail, try cleaning
                    repaired = clean_json_string(info_str)
                    info = json.loads(repaired)
                
                cred = credentials.Certificate(info)
                firebase_admin.initialize_app(cred)
            except Exception as e:
                # FINAL DIAGNOSTIC: Pinpoint the exact character if it still fails
                err_msg = str(e)
                snippet = f"{raw_input[:20]}...{raw_input[-20:]}"
                os.environ["FIREBASE_INIT_ERROR"] = f"{err_msg} | Type:{detected_type} | Snippet:{snippet}"
        
        if not firebase_admin._apps:
            try:
                firebase_admin.initialize_app()
            except:
                pass
    
    try:
        if firebase_admin._apps:
            _db = firestore.client()
            return _db
    except Exception as e:
        print(f"CRITICAL: Could not initialize Firestore client: {e}")
        return None
    return None

class FirestoreDB:
    @staticmethod
    def get_staff():
        db = get_db()
        if not db: return []
        docs = db.collection("staff").stream()
        staff_list = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            staff_list.append(data)
        return staff_list

    @staticmethod
    def get_staff_member(staff_id=None, name=None):
        db = get_db()
        if not db: return None
        if staff_id:
            doc = db.collection("staff").document(staff_id).get()
            if doc.exists:
                data = doc.to_dict()
                data["id"] = doc.id
                return data
        if name:
            docs = db.collection("staff").where("name", "==", name).limit(1).stream()
            for doc in docs:
                data = doc.to_dict()
                data["id"] = doc.id
                return data
        return None

    @staticmethod
    def get_schedules(staff_id, day=None):
        db = get_db()
        if not db: return []
        query = db.collection("staff").document(staff_id).collection("schedules")
        if day:
            query = query.where("day_of_week", "==", day)
        
        docs = query.stream()
        schedules = []
        for doc in docs:
            schedules.append(doc.to_dict())
        return schedules

    @staticmethod
    def add_absence(staff_id, staff_name, date, start_period, end_period):
        db = get_db()
        if not db: return None
        absence_ref = db.collection("absences").document()
        absence_data = {
            "staff_id": staff_id,
            "staff_name": staff_name,
            "date": date,
            "start_period": int(start_period),
            "end_period": int(end_period),
            "timestamp": firestore.SERVER_TIMESTAMP
        }
        absence_ref.set(absence_data)
        return absence_ref.id

    @staticmethod
    def get_absences(date=None, staff_id=None):
        db = get_db()
        if not db: return []
        query = db.collection("absences")
        if date:
            query = query.where("date", "==", date)
        if staff_id:
            query = query.where("staff_id", "==", staff_id)
        
        docs = query.stream()
        absences = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            covers_docs = db.collection("absences").document(doc.id).collection("covers").stream()
            data["covers"] = [c.to_dict() for c in covers_docs]
            absences.append(data)
        return absences

    @staticmethod
    def assign_cover(absence_id, staff_id, staff_name, period):
        db = get_db()
        if not db: return False
        cover_ref = db.collection("absences").document(absence_id).collection("covers").document(str(period))
        cover_data = {
            "covering_staff_id": staff_id,
            "covering_staff_name": staff_name,
            "period": int(period),
            "status": "confirmed"
        }
        cover_ref.set(cover_data)
        return True

    @staticmethod
    def unassign_cover(absence_id, period):
        db = get_db()
        if not db: return False
        db.collection("absences").document(absence_id).collection("covers").document(str(period)).delete()
        return True
