from google.cloud import firestore
from google.oauth2 import service_account
import os
import json
import re

# Global variables
_db = None

def reset_db():
    global _db
    _db = None
    print("FIRESTORE: Connection cleared for reset.")

def get_db(force_refresh=False):
    global _db
    if force_refresh:
        _db = None

    if _db is not None:
        return _db
        
    print("FIRESTORE: Initializing (v5.5.30 - Self-Healing)...")
    
    # Lazy imports to save memory on startup
    from google.cloud import firestore
    from google.oauth2 import service_account
    
    # 1. Pull and scrub quotes/whitespace from ALL variables
    pk = os.getenv("FIREBASE_PRIVATE_KEY", "").strip().strip('"').strip("'")
    email = os.getenv("FIREBASE_CLIENT_EMAIL", "").strip().strip('"').strip("'")
    project_id = os.getenv("FIREBASE_PROJECT_ID", "").strip().strip('"').strip("'")
    
    if not pk or not email or not project_id:
        print(f"FIRESTORE ERROR: Missing variables (P:{bool(project_id)} E:{bool(email)} K:{bool(pk)})")
        return None

    try:
        # 2. Extract Key Material
        pk_clean = pk.replace("\\n", "\n")
        parts = pk_clean.split("-----")
        meat = max(parts, key=len)
        
        # 3. PLUS RECOVERY STRATEGY
        if " " in meat and "+" not in meat:
            meat = meat.replace(" ", "+")
        
        # 4. FINAL CLEANSE
        meat = re.sub(r'[^A-Za-z0-9+/=]', '', meat)
        
        # 5. REBUILD PEM
        lines = [meat[i:i+64] for i in range(0, len(meat), 64)]
        clean_pk = "-----BEGIN PRIVATE KEY-----\n" + "\n".join(lines) + "\n-----END PRIVATE KEY-----\n"

        info = {
            "project_id": project_id,
            "private_key": clean_pk,
            "client_email": email,
            "token_uri": "https://oauth2.googleapis.com/token",
            "type": "service_account"
        }
        
        creds = service_account.Credentials.from_service_account_info(info)
        _db = firestore.Client(credentials=creds, project=project_id)
        
        print(f"FIRESTORE SUCCESS: (v5.5.30) - Key Length: {len(meat)}")
        return _db
    except Exception as e:
        print(f"FIRESTORE CRITICAL ERROR: {str(e)}")
        return None

class FirestoreDB:
    @staticmethod
    def get_staff():
        database = get_db()
        if not database: return []
        try:
            # We use a short timeout here to avoid the 300s hang
            docs = database.collection("staff").stream(timeout=10)
            staff_list = []
            for doc in docs:
                data = doc.to_dict()
                data["id"] = doc.id
                staff_list.append(data)
            return staff_list
        except Exception as e:
            msg = str(e)
            if "invalid_grant" in msg:
                print("AUTH ERROR: Invalid JWT Signature. Check your Private Key on Render.")
            else:
                print(f"Firestore get_staff Error: {msg}")
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
