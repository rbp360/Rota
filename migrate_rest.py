import os
import json
import time
import firebase_admin
from firebase_admin import credentials, firestore
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 1. SETUP
JSON_PATH = "rotaai-49847-firebase-adminsdk-fbsvc-59f11aeb6b.json"
DB_PATH = os.path.join("data_archive", "rota.db")

def migrate():
    print("--- FIRESTORE REST SYNC ---")
    
    # Initialize Firebase Admin with the JSON file
    # Certificate(path) is the most robust way
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(JSON_PATH)
            firebase_admin.initialize_app(cred)
        # Force REST transport to avoid gRPC 503s
        from google.cloud.firestore_v1.services.firestore.transports.rest import FirestoreRestTransport
        from google.cloud import firestore as cloud_firestore
        
        with open(JSON_PATH) as f:
            pid = json.load(f)["project_id"]
            
        # Get the actual credential from the firebase app
        creds = firebase_admin.get_app().credential.get_credential()
        
        db = cloud_firestore.Client(
            project=pid, 
            credentials=creds, 
            transport=FirestoreRestTransport()
        )
        print(f"Connected to {pid} via REST.")
    except Exception as e:
        print(f"Setup Error: {e}")
        return

    # Load local data
    try:
        from backend.database import Staff, Schedule, Absence, Cover
        engine = create_engine(f"sqlite:///./{DB_PATH}")
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
    except Exception as e:
        print(f"DB Error: {e}")
        return

    staff_mems = session.query(Staff).all()
    print(f"Transferring {len(staff_mems)} records...")

    for i, s in enumerate(staff_mems):
        try:
            # Atomic operation for one teacher
            print(f"Teacher {i+1}: {s.name}...", end="")
            
            # Use a batch per teacher to make it faster but still atomic
            batch = db.batch()
            
            staff_ref = db.collection("staff").document(str(s.id))
            batch.set(staff_ref, {
                "name": s.name,
                "role": s.role,
                "profile": s.profile,
                "is_active": s.is_active,
                "is_priority": s.is_priority,
                "is_specialist": s.is_specialist,
                "can_cover_periods": s.can_cover_periods
            })

            schedules = session.query(Schedule).filter(Schedule.staff_id == s.id).all()
            for sch in schedules:
                doc_id = f"{sch.day_of_week}_{sch.period}"
                batch.set(staff_ref.collection("schedules").document(doc_id), {
                    "day_of_week": sch.day_of_week,
                    "period": sch.period,
                    "activity": sch.activity,
                    "is_free": sch.is_free
                })
            
            batch.commit()
            print(" Done.")
            time.sleep(0.5) # Prevent rate limiting
            
        except Exception as e:
            print(f" Error: {e}")
            if "invalid_grant" in str(e):
                print("ABORTING: The Google Auth Token was refused.")
                return

    print("\n✅ MIGRATION FINISHED.")

if __name__ == "__main__":
    migrate()
