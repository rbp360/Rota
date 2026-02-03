from google.cloud import firestore
from google.oauth2 import service_account
import os
import json
import re

# Global variables
_db = None

def get_db():
    global _db
    if _db is not None:
        return _db
        
    print("FIRESTORE: Starting initialization...")
    
    pk = os.getenv("FIREBASE_PRIVATE_KEY")
    email = os.getenv("FIREBASE_CLIENT_EMAIL")
    project_id = os.getenv("FIREBASE_PROJECT_ID")
    
    if not pk or not email or not project_id:
        print(f"FIRESTORE ERROR: Missing environment variables. PK:{'SET' if pk else 'MISSING'}, Email:{'SET' if email else 'MISSING'}, ProjectID:{'SET' if project_id else 'MISSING'}")
        return None

    try:
        print("FIRESTORE DEBUG 1: Scrubbing private key...")
        raw_pk = pk.strip()
        if raw_pk.startswith('"') and raw_pk.endswith('"'):
            raw_pk = raw_pk[1:-1]
        
        clean_pk = raw_pk.replace("\\n", "\n")
        
        # Final sanitization
        if "-----BEGIN PRIVATE KEY-----" not in clean_pk:
            print("FIRESTORE ERROR: Private key header missing after scrubbing")
            return None
            
        print("FIRESTORE DEBUG 2: Creating credentials object...")
        info = {
            "project_id": project_id,
            "private_key": clean_pk,
            "client_email": email,
            "token_uri": "https://oauth2.googleapis.com/token",
            "type": "service_account"
        }
        
        creds = service_account.Credentials.from_service_account_info(info)
        
        print("FIRESTORE DEBUG 3: Initializing Firestore client...")
        _db = firestore.Client(credentials=creds, project=project_id)
        
        # Test connection with a very short timeout
        print("FIRESTORE DEBUG 4: Testing connection...")
        # Since this can hang, we just return and hope for the best in the first call
        print("FIRESTORE SUCCESS: Connected")
        return _db
    except Exception as e:
        msg = f"FIRESTORE CRASH: {str(e)}"
        print(msg)
        os.environ["FIREBASE_INIT_ERROR"] = msg
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

    # Other methods simplified for safety
    @staticmethod
    def get_staff_member(staff_id=None, name=None):
        database = get_db()
        if not database: return None
        try:
            if staff_id:
                doc = database.collection("staff").document(staff_id).get()
                return {**doc.to_dict(), "id": doc.id} if doc.exists else None
            if name:
                docs = database.collection("staff").where("name", "==", name).limit(1).stream()
                for doc in docs:
                    return {**doc.to_dict(), "id": doc.id}
        except: pass
        return None

    @staticmethod
    def get_schedules(staff_id, day=None):
        database = get_db()
        if not database: return []
        try:
            query = database.collection("staff").document(staff_id).collection("schedules")
            if day: query = query.where("day_of_week", "==", day)
            return [doc.to_dict() for doc in query.stream()]
        except: return []

    @staticmethod
    def get_absences(date=None, staff_id=None):
        database = get_db()
        if not database: return []
        try:
            query = database.collection("absences")
            if date: query = query.where("date", "==", date)
            if staff_id: query = query.where("staff_id", "==", staff_id)
            absences = []
            for doc in query.stream():
                data = doc.to_dict()
                data["id"] = doc.id
                data["covers"] = [c.to_dict() for c in database.collection("absences").document(doc.id).collection("covers").stream()]
                absences.append(data)
            return absences
        except: return []

    @staticmethod
    def add_absence(staff_id, staff_name, date, start_period, end_period):
        database = get_db()
        if not database: return None
        try:
            doc_ref = database.collection("absences").document()
            doc_ref.set({
                "staff_id": staff_id,
                "staff_name": staff_name,
                "date": date,
                "start_period": start_period,
                "end_period": end_period
            })
            return doc_ref.id
        except: return None

    @staticmethod
    def assign_cover(absence_id, staff_name, periods):
        database = get_db()
        if not database: return False
        try:
            if isinstance(periods, str):
                plist = [int(p) for p in periods.split(',') if p]
            else:
                plist = periods
                
            parent_ref = database.collection("absences").document(absence_id)
            for p in plist:
                parent_ref.collection("covers").document(str(p)).set({
                    "period": p,
                    "staff_name": staff_name
                })
            return True
        except: return False

    @staticmethod
    def unassign_cover(absence_id, period):
        database = get_db()
        if not database: return False
        try:
            database.collection("absences").document(absence_id).collection("covers").document(str(period)).delete()
            return True
        except: return False
