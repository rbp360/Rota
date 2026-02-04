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
        
    print("FIRESTORE: Initializing (v5.5.40 - Ironclad Hex Codec)...")
    
    from google.cloud import firestore
    from google.oauth2 import service_account
    import binascii
    import json
    
    # 1. Check for the NEW high-reliability Hex variable
    hex_key = os.getenv("FIREBASE_KEY_HEX", "").strip()
    
    if hex_key:
        try:
            # Reconstruct the ENTIRE JSON from hex (0% chance of corruption)
            json_data = json.loads(binascii.unhexlify(hex_key).decode('utf-8'))
            creds = service_account.Credentials.from_service_account_info(json_data)
            _db = firestore.Client(credentials=creds, project=json_data["project_id"])
            print("FIRESTORE SUCCESS: (v5.5.40) - Decoded via HEX.")
            return _db
        except Exception as e:
            print(f"FIRESTORE HEX DECODE ERROR: {e}")
            # Fallback to standard methods...

    # 2. LEGACY FALLBACK (The Old logic)
    pk = os.getenv("FIREBASE_PRIVATE_KEY", "").strip()
    email = os.getenv("FIREBASE_CLIENT_EMAIL", "").strip()
    project_id = os.getenv("FIREBASE_PROJECT_ID", "").strip()
    
    if not pk or not email or not project_id:
        print("FIRESTORE ERROR: No connection data found.")
        return None

    try:
        # Nuclear PEM scrubber for legacy pastes
        import re
        clean = pk.replace("\\n", " ").replace("-----", " ")
        chunks = re.findall(r'[A-Za-z0-9+/=]{100,}', clean)
        if not chunks: chunks = re.findall(r'[A-Za-z0-9+/=]{30,}', clean)
        meat = max(chunks, key=len).replace("=", "")
        while len(meat) % 4 != 0: meat += "="
        lines = [meat[i:i+64] for i in range(0, len(meat), 64)]
        clean_pk = "-----BEGIN PRIVATE KEY-----\n" + "\n".join(lines) + "\n-----END PRIVATE KEY-----\n"

        info = {
            "project_id": project_id, "private_key": clean_pk,
            "client_email": email, "token_uri": "https://oauth2.googleapis.com/token",
            "type": "service_account"
        }
        creds = service_account.Credentials.from_service_account_info(info)
        _db = firestore.Client(credentials=creds, project=project_id)
        print("FIRESTORE SUCCESS: (v5.5.40) - Decoded via Legacy String Scrubber.")
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

    @staticmethod
    def update_schedule(staff_id, day, period, activity, is_free):
        database = get_db()
        if not database: return False
        try:
            sched_id = f"{day}_{period}"
            database.collection("staff").document(staff_id).collection("schedules").document(sched_id).set({
                "day_of_week": day,
                "period": period,
                "activity": activity,
                "is_free": is_free
            })
            return True
        except: return False

    @staticmethod
    def update_staff(staff_id, data):
        database = get_db()
        if not database: return False
        try:
            database.collection("staff").document(staff_id).update(data)
            return True
        except: return False
