import firebase_admin
from firebase_admin import credentials, firestore
import os
import json

# Global variables
_db = None

def get_db():
    global _db
    if _db is not None:
        return _db
        
    if not firebase_admin._apps:
        # 1. Individual Variables (Vercel)
        pk = os.getenv("FIREBASE_PRIVATE_KEY")
        email = os.getenv("FIREBASE_CLIENT_EMAIL")
        project_id = os.getenv("FIREBASE_PROJECT_ID")
        
        if pk and email and project_id:
            try:
                clean_pk = pk.replace("\\n", "\n").strip()
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
                os.environ["FIREBASE_INIT_ERROR"] = f"v1.3.1 | Individual Vars Failed: {str(e)}"

        # 2. Local JSON File (Development)
        if not firebase_admin._apps:
            # Look for the specific json file in the root
            possible_path = os.path.join(os.getcwd(), "rotaai-49847-firebase-adminsdk-fbsvc-59f11aeb6b.json")
            if os.path.exists(possible_path):
                try:
                    cred = credentials.Certificate(possible_path)
                    firebase_admin.initialize_app(cred)
                except Exception as e:
                    print(f"Failed to load local firebase key: {e}")

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
    except:
        pass
    return None

# For backward compatibility with migration scripts
@property
def db():
    return get_db()

# We need a real 'db' object at the top level for migration scripts that do 'from ... import db'
# But since get_db might fail initially, we can't just set it once at import time.
# However, many scripts expect it. Let's provide a proxy or just initialize it.
db = get_db()

class FirestoreDB:
    @staticmethod
    def get_staff():
        database = get_db()
        if not database: return []
        docs = database.collection("staff").stream()
        staff_list = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            staff_list.append(data)
        return staff_list

    @staticmethod
    def get_staff_member(staff_id=None, name=None):
        database = get_db()
        if not database: return None
        if staff_id:
            doc = database.collection("staff").document(staff_id).get()
            if doc.exists:
                data = doc.to_dict()
                data["id"] = doc.id
                return data
        if name:
            docs = database.collection("staff").where("name", "==", name).limit(1).stream()
            for doc in docs:
                data = doc.to_dict()
                data["id"] = doc.id
                return data
        return None

    @staticmethod
    def get_schedules(staff_id, day=None):
        database = get_db()
        if not database: return []
        query = database.collection("staff").document(staff_id).collection("schedules")
        if day:
            query = query.where("day_of_week", "==", day)
        
        docs = query.stream()
        schedules = []
        for doc in docs:
            schedules.append(doc.to_dict())
        return schedules

    @staticmethod
    def add_absence(staff_id, staff_name, date, start_period, end_period):
        database = get_db()
        if not database: return None
        absence_ref = database.collection("absences").document()
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
        database = get_db()
        if not database: return []
        query = database.collection("absences")
        if date:
            query = query.where("date", "==", date)
        if staff_id:
            query = query.where("staff_id", "==", staff_id)
        
        docs = query.stream()
        absences = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            covers_docs = database.collection("absences").document(doc.id).collection("covers").stream()
            data["covers"] = [c.to_dict() for c in covers_docs]
            absences.append(data)
        return absences

    @staticmethod
    def assign_cover(absence_id, staff_id, staff_name, period):
        database = get_db()
        if not database: return False
        cover_ref = database.collection("absences").document(absence_id).collection("covers").document(str(period))
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
        database = get_db()
        if not database: return False
        database.collection("absences").document(absence_id).collection("covers").document(str(period)).delete()
        return True
