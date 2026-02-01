import firebase_admin
from firebase_admin import credentials, firestore
import os
import json

# Global variable for the firestore client
_db = None

def get_db():
    global _db
    if _db is not None:
        return _db
        
    if not firebase_admin._apps:
        # 1. Try Individual Variables (The most stable method for Vercel)
        pk = os.getenv("FIREBASE_PRIVATE_KEY")
        email = os.getenv("FIREBASE_CLIENT_EMAIL")
        project_id = os.getenv("FIREBASE_PROJECT_ID")
        
        if pk and email and project_id:
            try:
                # Clean the private key: replace literal \n with real newlines
                clean_pk = pk.replace("\\n", "\n").strip()
                # If it's wrapped in quotes, strip them
                if clean_pk.startswith('"') and clean_pk.endswith('"'):
                    clean_pk = clean_pk[1:-1]
                
                info = {
                    "type": "service_account",
                    "project_id": project_id,
                    "private_key": clean_pk,
                    "client_email": email,
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
                cred = credentials.Certificate(info)
                firebase_admin.initialize_app(cred)
            except Exception as e:
                os.environ["FIREBASE_INIT_ERROR"] = f"v1.3.0 | Individual Vars Failed: {str(e)}"

        # 2. Fallback to the old JSON blob (if still set)
        if not firebase_admin._apps:
            service_account_info = os.getenv("FIREBASE_SERVICE_ACCOUNT")
            if service_account_info:
                try:
                    # Very basic JSON load
                    raw = service_account_info.strip()
                    if raw.startswith('"') and raw.endswith('"'): raw = raw[1:-1]
                    info = json.loads(raw)
                    if "private_key" in info:
                        info["private_key"] = info["private_key"].replace("\\n", "\n")
                    cred = credentials.Certificate(info)
                    firebase_admin.initialize_app(cred)
                except Exception as e:
                    os.environ["FIREBASE_INIT_ERROR"] = f"v1.3.0 | JSON Fallback Failed: {str(e)}"
        
        # 3. Last resort: Default credentials
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
        print(f"CRITICAL: {e}")
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
