import os
import json
import time

# 🆘 FORCE CLEAR EVERYTHING
for key in ["GOOGLE_APPLICATION_CREDENTIALS", "FIREBASE_SERVICE_ACCOUNT", "FIREBASE_PRIVATE_KEY", "FIREBASE_CLIENT_EMAIL", "FIREBASE_PROJECT_ID"]:
    if key in os.environ:
        del os.environ[key]

import firebase_admin
from firebase_admin import credentials, firestore
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def connect_db():
    json_path = "rotaai-49847-firebase-adminsdk-fbsvc-59f11aeb6b.json"
    if not os.path.exists(json_path):
        print(f"ERROR: {json_path} missing!")
        return None
    
    try:
        with open(json_path, 'r') as f:
            info = json.load(f)
        
        # SANITIZE PRIVATE KEY (The most common cause of JWT Signature errors)
        if "private_key" in info:
            # Replace double backslashes with single real newlines
            pk = info["private_key"]
            pk = pk.replace("\\n", "\n")
            info["private_key"] = pk
            
        if not firebase_admin._apps:
            cred = credentials.Certificate(info)
            firebase_admin.initialize_app(cred)
            print("Connected to Firestore via sanitized JSON.")
        return firestore.client()
    except Exception as e:
        print(f"Failed to connect: {e}")
        return None

def migrate():
    db = connect_db()
    if not db: return

    db_path = os.path.join("data_archive", "rota.db")
    if not os.path.exists(db_path):
        print("Archive DB not found.")
        return

    # Importing models here
    from backend.database import Staff, Schedule
    
    engine = create_engine(f"sqlite:///./{db_path}")
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    staff_mems = session.query(Staff).all()
    print(f"Uploading {len(staff_mems)} teachers...")

    for s in staff_mems:
        # Retry logic
        for attempt in range(3):
            try:
                sid = str(s.id)
                sref = db.collection("staff").document(sid)
                sref.set({
                    "name": s.name,
                    "role": s.role,
                    "profile": s.profile,
                    "is_priority": s.is_priority,
                    "is_specialist": s.is_specialist,
                    "is_active": s.is_active,
                    "can_cover_periods": s.can_cover_periods,
                    "calendar_url": s.calendar_url
                })
                
                # Upload Schedules
                scheds = session.query(Schedule).filter(Schedule.staff_id == s.id).all()
                for sch in scheds:
                    sref.collection("schedules").document(f"{sch.day_of_week}_{sch.period}").set({
                        "day_of_week": sch.day_of_week,
                        "period": sch.period,
                        "activity": sch.activity,
                        "is_free": sch.is_free
                    })
                print(f"  [DONE] {s.name}")
                break
            except Exception as e:
                print(f"  [FAIL] {s.name} (Attempt {attempt+1}): {e}")
                time.sleep(3)

    print("\nFINISH.")

if __name__ == "__main__":
    migrate()
