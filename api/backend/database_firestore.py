from google.cloud import firestore
import os
import json

# Global variable for the firestore client
_db = None

def get_db():
    global _db
    if _db is not None:
        return _db
    
    # 1. Individual Variables (Vercel)
    pk = os.getenv("FIREBASE_PRIVATE_KEY")
    email = os.getenv("FIREBASE_CLIENT_EMAIL")
    project_id = os.getenv("FIREBASE_PROJECT_ID")
    
    if pk and email and project_id:
        try:
            # Clean up private key
            clean_pk = pk.replace("\\n", "\n").strip()
            if clean_pk.startswith('"') and clean_pk.endswith('"'):
                clean_pk = clean_pk[1:-1]
            
            # Use google-cloud-firestore compatible credentials
            from google.oauth2 import service_account
            info = {
                "project_id": project_id,
                "private_key": clean_pk,
                "client_email": email,
                "token_uri": "https://oauth2.googleapis.com/token",
            }
            creds = service_account.Credentials.from_service_account_info(info)
            _db = firestore.Client(credentials=creds, project=project_id)
            return _db
        except Exception as e:
            os.environ["FIREBASE_INIT_ERROR"] = f"v1.8.0 | Lighter Init Failed: {str(e)}"

    # 2. Local JSON File (Development)
    possible_path = os.path.join(os.getcwd(), "rotaai-49847-firebase-adminsdk-fbsvc-59f11aeb6b.json")
    if os.path.exists(possible_path):
        try:
            _db = firestore.Client.from_service_account_json(possible_path)
            return _db
        except Exception as e:
            print(f"Failed to load local firebase key: {e}")
            
    return None

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
