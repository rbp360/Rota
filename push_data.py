import firebase_admin
from firebase_admin import credentials, firestore
import os
import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 1. LOCAL FIREBASE CONNECTION (Directly from file)
def connect_db():
    json_path = "rotaai-49847-firebase-adminsdk-fbsvc-59f11aeb6b.json"
    print(f"Checking for {json_path}...")
    
    if not os.path.exists(json_path):
        print(f"CRITICAL: {json_path} not found in this folder!")
        return None

    if not firebase_admin._apps:
        try:
            print("Connecting to Firestore using JSON file...")
            cred = credentials.Certificate(json_path)
            firebase_admin.initialize_app(cred)
            print("Connected successfully!")
        except Exception as e:
            print(f"Failed to connect: {e}")
            return None
    return firestore.client()

# 2. MIGRATION LOGIC
def migrate():
    db = connect_db()
    if not db: return

    # Setup SQLite (using your archive DB)
    db_path = os.path.join("data_archive", "rota.db")
    if not os.path.exists(db_path):
        print(f"Local SQLite DB not found at {db_path}")
        return

    # Dynamic imports to avoid dependency issues in this script
    try:
        from backend.database import Staff
    except ImportError:
        print("Backend models not found. Please ensure you are running from the Rota root folder.")
        return

    SQLALCHEMY_DATABASE_URL = f"sqlite:///./{db_path}"
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    print("Reading staff from SQLite...")
    staff_members = session.query(Staff).all()
    print(f"Found {len(staff_members)} teachers. Uploading to Cloud...")
    
    count = 0
    for s in staff_members:
        try:
            staff_id = str(s.id)
            # Use a batch or individual set
            db.collection("staff").document(staff_id).set({
                "name": s.name,
                "role": s.role,
                "profile": s.profile,
                "is_priority": s.is_priority,
                "is_specialist": s.is_specialist,
                "is_active": s.is_active,
                "can_cover_periods": s.can_cover_periods,
                "calendar_url": s.calendar_url
            })
            count += 1
            if count % 5 == 0:
                print(f"  - Uploaded {count} so far...")
        except Exception as e:
            print(f"  - Error uploading {s.name}: {e}")

    print(f"\nSUCCESS! {count} teachers are now in the Cloud.")
    print("Refresh your health check URL to see the new 'staff_count'.")

if __name__ == "__main__":
    migrate()
