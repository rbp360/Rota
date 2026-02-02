from google.cloud import firestore
from google.oauth2 import service_account
import os
import json

# Global variables
_db = None

def get_db():
    global _db
    if _db is not None:
        return _db
        
    print("INITIALIZING FIRESTORE (LITE)...")
    
    # 1. Individual Variables (Vercel)
    pk = os.getenv("FIREBASE_PRIVATE_KEY")
    email = os.getenv("FIREBASE_CLIENT_EMAIL")
    project_id = os.getenv("FIREBASE_PROJECT_ID")
    
    if pk and email and project_id:
        try:
            # SUPER AGGRESSIVE PK CLEANING
            # 1. Remove literal quotes if they exist at ends
            pk = pk.strip()
            if pk.startswith('"') and pk.endswith('"'):
                pk = pk[1:-1]
            if pk.startswith("'") and pk.endswith("'"):
                pk = pk[1:-1]
            
            # 2. Handle escaped newlines (\n) vs real newlines
            # If the user pasted it with \n characters, we replace them.
            # If they are real newlines, this won't hurt.
            clean_pk = pk.replace("\\n", "\n")
            
            # 3. Final verification of header/footer
            if "-----BEGIN PRIVATE KEY-----" not in clean_pk:
                print("WARNING: MISSING PRIVATE KEY HEADER")
            
            info = {
                "project_id": project_id,
                "private_key": clean_pk,
                "client_email": email,
                "token_uri": "https://oauth2.googleapis.com/token",
                "type": "service_account"
            }
            creds = service_account.Credentials.from_service_account_info(info)
            _db = firestore.Client(credentials=creds, project=project_id)
            print("FIRESTORE CONNECTED (ENV)")
            return _db
        except Exception as e:
            msg = f"Firestore Init Failed (Env): {str(e)}"
            print(msg)
            os.environ["FIREBASE_INIT_ERROR"] = msg

    # 2. Local JSON File (Development)
    possible_path = os.path.join(os.getcwd(), "rotaai-49847-firebase-adminsdk-fbsvc-59f11aeb6b.json")
    if os.path.exists(possible_path):
        try:
            _db = firestore.Client.from_service_account_json(possible_path)
            print("FIRESTORE CONNECTED (JSON)")
            return _db
        except Exception as e:
            print(f"Failed to load local firebase key: {e}")

    print("FIRESTORE NOT CONNECTED")
    return None

class FirestoreDB:
    @staticmethod
    def get_staff():
        database = get_db()
        if not database: return []
        try:
            docs = database.collection("staff").stream()
            staff_list = []
            for doc in docs:
                data = doc.to_dict()
                data["id"] = doc.id
                staff_list.append(data)
            return staff_list
        except Exception as e:
            print(f"Firestore get_staff Error: {e}")
            return []

    @staticmethod
    def get_staff_member(staff_id=None, name=None):
        database = get_db()
        if not database: return None
        try:
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
        except: pass
        return None

    @staticmethod
    def get_schedules(staff_id, day=None):
        database = get_db()
        if not database: return []
        try:
            query = database.collection("staff").document(staff_id).collection("schedules")
            if day:
                query = query.where("day_of_week", "==", day)
            docs = query.stream()
            schedules = []
            for doc in docs:
                schedules.append(doc.to_dict())
            return schedules
        except: return []

    @staticmethod
    def add_absence(staff_id, staff_name, date, start_period, end_period):
        database = get_db()
        if not database: return None
        try:
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
        except: return None

    @staticmethod
    def get_absences(date=None, staff_id=None):
        database = get_db()
        if not database: return []
        try:
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
        except: return []
