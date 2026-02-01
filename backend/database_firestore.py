import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
import binascii

# Global variable for the firestore client
_db = None

def get_db():
    global _db
    if _db is not None:
        return _db
        
    if not firebase_admin._apps:
        service_account_info = os.getenv("FIREBASE_SERVICE_ACCOUNT")
        
        if service_account_info:
            # Clean input
            raw_input = "".join(service_account_info.split()).strip()
            if raw_input.startswith(('"', "'")) and raw_input.endswith(('"', "'")):
                raw_input = raw_input[1:-1]

            try:
                # 1. Decode the Hex
                if all(c in '0123456789abcdefABCDEF' for c in raw_input) and len(raw_input) > 500:
                    decoded_str = binascii.unhexlify(raw_input).decode('utf-8')
                    info = json.loads(decoded_str)
                else:
                    # Fallback for raw JSON
                    import base64
                    if raw_input.startswith('{'):
                        info = json.loads(raw_input)
                    else:
                        decoded_bytes = base64.b64decode(raw_input)
                        info = json.loads(decoded_bytes.decode('utf-8'))
                
                # 2. NUCLEAR REPAIR of the Private Key
                # This fixes the "Unable to load PEM file" error by ensuring 
                # newlines are literal \n characters in the string.
                if "private_key" in info:
                    pk = info["private_key"]
                    # Replace literal \n symbols with real newline characters
                    pk = pk.replace("\\n", "\n")
                    # Ensure it has the correct BEGIN/END markers with no extra whitespace
                    info["private_key"] = pk.strip()

                cred = credentials.Certificate(info)
                firebase_admin.initialize_app(cred)
            except Exception as e:
                os.environ["FIREBASE_INIT_ERROR"] = f"v1.2.1 | {str(e)} | Len:{len(raw_input)}"
        
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
