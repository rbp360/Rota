import firebase_admin
from firebase_admin import credentials, firestore
import os
from datetime import datetime

import json

# Global variable for the firestore client
_db = None

def get_db():
    global _db
    if _db is not None:
        return _db
        
    if not firebase_admin._apps:
        # 1. Try to load from "FIREBASE_SERVICE_ACCOUNT" environment variable
        service_account_info = os.getenv("FIREBASE_SERVICE_ACCOUNT")
        
            # Detect if it's Base64 or Raw JSON
            import base64
            raw_info = service_account_info.strip()
            detected_type = "b64" if not raw_info.startswith('{') else "json"
            
            try:
                if detected_type == "b64":
                    decoded = base64.b64decode(raw_info).decode('utf-8')
                    info = json.loads(decoded)
                else:
                    # Clean up mangled JSON
                    cleaned = raw_info
                    if cleaned.startswith("'") or cleaned.startswith('"'):
                        cleaned = cleaned[1:-1]
                    # Fix escapes: Vercel sometimes double-escapes \n or \/
                    cleaned = cleaned.replace('\\\\', '\\')
                    cleaned = cleaned.replace('\\n', '\n').replace('\n', '\\n')
                    info = json.loads(cleaned)
                
                cred = credentials.Certificate(info)
                firebase_admin.initialize_app(cred)
            except Exception as e:
                snippet = f"{raw_info[:20]}...{raw_info[-20:]}"
                os.environ["FIREBASE_INIT_ERROR"] = f"Type:{detected_type} | Err:{str(e)} | Len:{len(raw_info)} | Snippet:{snippet}"
        
        # 2. Try Default Application Credentials (useful if running in Google Cloud environment)
        if not firebase_admin._apps:
            try:
                firebase_admin.initialize_app()
            except:
                pass

        # 3. Fallback to local file if not already initialized
        if not firebase_admin._apps:
            SERVICE_ACCOUNT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "rotaai-49847-firebase-adminsdk-fbsvc-59f11aeb6b.json")
            if os.path.exists(SERVICE_ACCOUNT_PATH):
                try:
                    cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
                    firebase_admin.initialize_app(cred)
                except Exception as e:
                    print(f"Error loading local service account: {e}")
    
    try:
        _db = firestore.client()
        return _db
    except Exception as e:
        print(f"CRITICAL: Could not initialize Firestore client: {e}")
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
        # date should be string "YYYY-MM-DD"
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
            # Fetch covers
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
