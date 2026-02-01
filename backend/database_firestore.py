import firebase_admin
from firebase_admin import credentials, firestore
import os
from datetime import datetime
import json
import base64

# Global variable for the firestore client
_db = None

def get_db():
    global _db
    if _db is not None:
        return _db
        
    if not firebase_admin._apps:
        # 1. Try to load from "FIREBASE_SERVICE_ACCOUNT" environment variable
        service_account_info = os.getenv("FIREBASE_SERVICE_ACCOUNT")
        
        if service_account_info:
            raw_info = service_account_info.strip()
            # Remove any wrapping quotes that Vercel might have added
            if raw_info.startswith('"') and raw_info.endswith('"'):
                raw_info = raw_info[1:-1]
            if raw_info.startswith("'") and raw_info.endswith("'"):
                raw_info = raw_info[1:-1]
                
            detected_type = "b64" if not raw_info.startswith('{') else "json"
            
            try:
                if detected_type == "b64":
                    decoded = base64.b64decode(raw_info).decode('utf-8')
                    # Apply cleaning to the decoded string too!
                    cleaned = decoded.replace('\\\\', '\\').replace('\\n', '\n').replace('\n', '\\n')
                    try:
                        info = json.loads(cleaned)
                    except:
                        # If cleaning made it worse, try the raw decoded string
                        info = json.loads(decoded)
                else:
                    # Clean up mangled JSON
                    cleaned = raw_info.replace('\\\\', '\\').replace('\\n', '\n').replace('\n', '\\n')
                    info = json.loads(cleaned)
                
                cred = credentials.Certificate(info)
                firebase_admin.initialize_app(cred)
            except Exception as e:
                snippet = f"{raw_info[:20]}...{raw_info[-20:]}"
                os.environ["FIREBASE_INIT_ERROR"] = f"Type:{detected_type} | Err:{str(e)} | Snippet:{snippet}"
        
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
