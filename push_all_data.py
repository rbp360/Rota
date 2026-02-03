import firebase_admin
from firebase_admin import credentials, firestore
import os
import sqlite3
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 🆘 STEP 1: RESET ALL LOCAL AUTH CACHES
print("Resetting local auth environment...")
for key in ["GOOGLE_APPLICATION_CREDENTIALS", "FIREBASE_SERVICE_ACCOUNT", "FIREBASE_PRIVATE_KEY", "FIREBASE_CLIENT_EMAIL", "FIREBASE_PROJECT_ID"]:
    if key in os.environ:
        del os.environ[key]

# 2. CONNECT (SIMPLEST WAY POSSIBLE)
def connect_firestore():
    json_path = "rotaai-49847-firebase-adminsdk-fbsvc-59f11aeb6b.json"
    print(f"Loading credentials from: {json_path}")
    
    if not os.path.exists(json_path):
        print("ERROR: File not found!")
        return None

    try:
        if firebase_admin._apps:
            for app_name in list(firebase_admin._apps.keys()):
                firebase_admin.delete_app(firebase_admin.get_app(app_name))

        # We load the file NORMALLY first. 
        # Only if that fails do we try "Ironclad" logic.
        cred = credentials.Certificate(json_path)
        firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception as e:
        print(f"Normal initialization failed: {e}")
        print("Attempting to repair the key in memory...")
        
        try:
            import json, re
            with open(json_path, 'r') as f:
                data = json.load(f)
            
            # Extract just the Base64 data
            raw_key = data['private_key']
            meat = re.sub(r'-----BEGIN PRIVATE KEY-----|-----END PRIVATE KEY-----|\n|\\n| ', '', raw_key)
            # Rebuild with standard PEM formatting (64 chars per line)
            lines = [meat[i:i+64] for i in range(0, len(meat), 64)]
            fixed_key = "-----BEGIN PRIVATE KEY-----\n" + "\n".join(lines) + "\n-----END PRIVATE KEY-----\n"
            data['private_key'] = fixed_key
            
            cred = credentials.Certificate(data)
            firebase_admin.initialize_app(cred)
            return firestore.client()
        except Exception as e2:
            print(f"Repair attempt failed: {e2}")
            return None

def sync():
    db = connect_firestore()
    if not db: 
        print("CRITICAL: Could not connect to Cloud. Check if your JSON file is corrupted.")
        return

    db_path = os.path.join("data_archive", "rota.db")
    if not os.path.exists(db_path):
        print(f"Archive missing: {db_path}")
        return

    from backend.database import Staff, Schedule, Absence, Cover
    engine = create_engine(f"sqlite:///./{db_path}")
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    staff_mems = session.query(Staff).all()
    print(f"\nPhase 1: Syncing {len(staff_mems)} staff...")
    
    for s in staff_mems:
        try:
            sid = str(s.id)
            staff_ref = db.collection("staff").document(sid)
            staff_ref.set({
                "name": s.name,
                "role": s.role,
                "profile": s.profile,
                "is_priority": s.is_priority,
                "is_specialist": s.is_specialist,
                "is_active": s.is_active,
                "can_cover_periods": s.can_cover_periods,
                "calendar_url": s.calendar_url
            }, timeout=30)
            
            # Schedules
            sches = session.query(Schedule).filter(Schedule.staff_id == s.id).all()
            for sch in sches:
                staff_ref.collection("schedules").document(f"{sch.day_of_week}_{sch.period}").set({
                    "day_of_week": sch.day_of_week, "period": sch.period, "activity": sch.activity, "is_free": sch.is_free
                }, timeout=10)
            
            print(f"  [OK] {s.name}")
        except Exception as e:
            print(f"  [FAIL] {s.name}: {e}")
            time.sleep(1)

    print("\n✅ SYNC FINISHED.")

if __name__ == "__main__":
    sync()
