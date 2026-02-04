import os
import json
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 1. CONFIGURATION
JSON_PATH = "rotaai-49847-d923810f254e.json"
DB_PATH = os.path.join("data_archive", "rota.db")

def connect_firestore():
    from google.cloud import firestore
    from google.oauth2 import service_account
    
    print("\n--- CONNECTING TO FIRESTORE (DIRECT CERT) ---")
    
    try:
        # Load the raw file
        if not os.path.exists(JSON_PATH):
            print(f"ERROR: {JSON_PATH} not found!")
            return None
            
        with open(JSON_PATH) as f:
            info = json.load(f)
            project_id = info["project_id"]
            
        # Create credentials directly from the file
        creds = service_account.Credentials.from_service_account_info(info)
        
        print(f"Project: {project_id}")
        
        # Initialize the client with EXPLICIT credentials 
        # This fixes the 'Your default credentials were not found' error
        return firestore.Client(
            project=project_id, 
            credentials=creds
        )
    except Exception as e:
        print(f"CRITICAL CONNECTION ERROR: {e}")
        return None

def migrate():
    print(f"Current Local Time: {time.ctime()}")
    db = connect_firestore()
    if not db: return

    try:
        from backend.database import Staff, Schedule, Absence, Cover
        engine = create_engine(f"sqlite:///./{DB_PATH}")
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
    except Exception as e:
        print(f"Error loading SQLite: {e}")
        return

    staff_mems = session.query(Staff).all()
    print(f"\nPushing {len(staff_mems)} staff to cloud...")

    for i, s in enumerate(staff_mems):
        try:
            staff_ref = db.collection("staff").document(str(s.id))
            staff_ref.set({
                "name": s.name,
                "role": s.role,
                "profile": s.profile,
                "is_priority": s.is_priority,
                "is_specialist": s.is_specialist,
                "is_active": s.is_active,
                "can_cover_periods": s.can_cover_periods,
                "calendar_url": s.calendar_url
            })

            # Sub-collection: Schedules
            schedules = session.query(Schedule).filter(Schedule.staff_id == s.id).all()
            for sch in schedules:
                doc_id = f"{sch.day_of_week}_{sch.period}"
                staff_ref.collection("schedules").document(doc_id).set({
                    "day_of_week": sch.day_of_week,
                    "period": sch.period,
                    "activity": sch.activity,
                    "is_free": sch.is_free
                })
            
            print(f"  [{i+1}/{len(staff_mems)}] ✅ {s.name}")
        except Exception as e:
            print(f"  ❌ FAIL on {s.name}: {e}")
            if "invalid_grant" in str(e):
                print("\nAUTH ERROR: Still getting 'Invalid JWT Signature'.")
                print("If you have ALREADY synced your Windows clock, the JSON key might be revoked.")
                return

    print("\n🎉 SYNC COMPLETE!")

if __name__ == "__main__":
    migrate()
