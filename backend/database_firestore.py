import firebase_admin
from firebase_admin import credentials, firestore
import os
from datetime import datetime
import json
import base64
import re

# Global variable for the firestore client
_db = None

def heal_json(s):
    """
    Scans for illegal backslashes in JSON and fixes them.
    Only \", \\, \/, \b, \f, \n, \r, \t, \u are allowed.
    """
    def replacer(match):
        esc = match.group(0)
        if len(esc) < 2: return esc
        if esc[1] in 'bfnrtu"\\\\/':
            return esc
        # If it's invalid (like \m or \ ), double the backslash to make it a literal backslash
        return '\\\\' + esc[1]
    return re.sub(r'\\\\.', replacer, s)

def get_db():
    global _db
    if _db is not None:
        return _db
        
    if not firebase_admin._apps:
        service_account_info = os.getenv("FIREBASE_SERVICE_ACCOUNT")
        
        if service_account_info:
            raw_info = service_account_info.strip()
            # Remove wrapping quotes
            if raw_info.startswith('"') and raw_info.endswith('"'):
                raw_info = raw_info[1:-1]
            if raw_info.startswith("'") and raw_info.endswith("'"):
                raw_info = raw_info[1:-1]
                
            detected_type = "b64" if not raw_info.startswith('{') else "json"
            
            try:
                if detected_type == "b64":
                    # Step 1: Decode
                    decoded_bytes = base64.b64decode(raw_info)
                    decoded_str = decoded_bytes.decode('utf-8')
                    # Step 2: Heal logic
                    # First, turn literal newlines into \n symbols
                    cleaned = decoded_str.replace('\n', '\\n').replace('\r', '')
                    # Then fix double escaping
                    cleaned = cleaned.replace('\\\\n', '\\n')
                    try:
                        info = json.loads(cleaned)
                    except:
                        # Fallback: Heal illegal escapes
                        info = json.loads(heal_json(cleaned))
                else:
                    cleaned = heal_json(raw_info.replace('\n', '\\n'))
                    info = json.loads(cleaned)
                
                cred = credentials.Certificate(info)
                firebase_admin.initialize_app(cred)
            except Exception as e:
                err_msg = str(e)
                char_info = ""
                # X-RAY: Find the exact character that failed
                match = re.search(r'\(char (\d+)\)', err_msg)
                if match:
                    idx = int(match.group(1))
                    # Use the raw string we tried to parse
                    target = cleaned if 'cleaned' in locals() else raw_info
                    snippet = target[max(0, idx-10):min(len(target), idx+10)]
                    char_info = f" | At{idx}:[{snippet}]"
                
                os.environ["FIREBASE_INIT_ERROR"] = f"{err_msg}{char_info}"
        
        # 2. Try Default Application Credentials
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
