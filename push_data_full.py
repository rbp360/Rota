import firebase_admin
from firebase_admin import credentials, firestore
import os
import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 1. LOCAL FIREBASE CONNECTION
def connect_db():
    json_path = "rotaai-49847-firebase-adminsdk-fbsvc-59f11aeb6b.json"
    if not firebase_admin._apps:
        try:
            cred = credentials.Certificate(json_path)
            firebase_admin.initialize_app(cred)
        except Exception as e:
            print(f"Failed to connect: {e}")
            return None
    return firestore.client()

# 2. FULL MIGRATION
def migrate():
    db = connect_db()
    if not db: return

    db_path = os.path.join("data_archive", "rota.db")
    if not os.path.exists(db_path):
        print(f"Local SQLite DB not found at {db_path}")
        return

    try:
        from backend.database import Staff, Schedule
    except ImportError:
        print("Backend models not found.")
        return

    SQLALCHEMY_DATABASE_URL = f"sqlite:///./{db_path}"
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    staff_members = session.query(Staff).all()
    print(f"Migrating {len(staff_members)} teachers AND their schedules...")
    
    for s in staff_members:
        try:
            staff_id = str(s.id)
            staff_ref = db.collection("staff").document(staff_id)
            
            # Update/Set staff info
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

            # Upload Schedules
            schedules = session.query(Schedule).filter(Schedule.staff_id == s.id).all()
            for sch in schedules:
                doc_id = f"{sch.day_of_week}_{sch.period}"
                staff_ref.collection("schedules").document(doc_id).set({
                    "day_of_week": sch.day_of_week,
                    "period": sch.period,
                    "activity": sch.activity,
                    "is_free": sch.is_free
                })
            print(f"  [OK] {s.name}")
        except Exception as e:
            print(f"  [ERROR] {s.name}: {e}")

    print("\n--- MIGRATION COMPLETE ---")

if __name__ == "__main__":
    migrate()
