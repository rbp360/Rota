import os
import json
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from google.cloud import firestore
from google.oauth2 import service_account

JSON_PATH = "rotaai-49847-d923810f254e.json"
DB_PATH = os.path.join("data_archive", "rota.db")

def get_db():
    with open(JSON_PATH) as f:
        info = json.load(f)
    creds = service_account.Credentials.from_service_account_info(info)
    return firestore.Client(project=info["project_id"], credentials=creds)

def migrate():
    print("--- SUPER-ROBUST INDIVIDUAL SYNC ---")
    
    try:
        from backend.database import Staff, Schedule, Absence, Cover
        engine = create_engine(f"sqlite:///./{DB_PATH}")
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
    except Exception as e:
        print(f"DB Error: {e}")
        return

    staff_members = session.query(Staff).all()
    print(f"Total staff: {len(staff_members)}")

    for i, s in enumerate(staff_members):
        print(f"[{i+1}/{len(staff_members)}] Syncing {s.name}...")
        
        # We RE-CONNECT for every teacher to ensure fresh auth
        try:
            db = get_db()
            staff_ref = db.collection("staff").document(str(s.id))
            
            # Simple Write
            staff_ref.set({
                "name": s.name,
                "role": s.role,
                "is_active": s.is_active
            })
            
            # Schedules
            schedules = session.query(Schedule).filter(Schedule.staff_id == s.id).all()
            for sch in schedules:
                staff_ref.collection("schedules").document(f"{sch.day_of_week}_{sch.period}").set({
                    "day_of_week": sch.day_of_week,
                    "period": sch.period,
                    "activity": sch.activity,
                    "is_free": sch.is_free
                })
            
            print(f"  ✅ {s.name} synced.")
            # Clear DB object to free memory
            del db
            
        except Exception as e:
            print(f"  ❌ FAILED {s.name}: {e}")
            if "invalid_grant" in str(e):
                print("Stopping: Auth Token Rejected.")
                return

    print("\nDraft Sync Finished.")

if __name__ == "__main__":
    migrate()
