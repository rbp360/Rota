import os
import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database import Base, Staff, Schedule, Absence, Cover
from backend.database_firestore import get_db, firestore

def migrate():
    print("Initializing migration...")
    db = get_db()
    if not db:
        print("ERROR: Could not connect to Firestore!")
        return

    # Setup SQLite
    db_path = os.path.join("data_archive", "rota.db")
    if not os.path.exists(db_path):
        print(f"ERROR: Local DB not found at {db_path}")
        return

    SQLALCHEMY_DATABASE_URL = f"sqlite:///./{db_path}"
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    print("Starting migration to Firestore...")

    # 1. Migrate Staff
    staff_members = session.query(Staff).all()
    print(f"Migrating {len(staff_members)} staff members...")
    
    for s in staff_members:
        staff_id = str(s.id)
        staff_ref = db.collection("staff").document(staff_id)
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
        print(f"  - Migrated {s.name}")

    print("Migration complete!")

if __name__ == "__main__":
    migrate()
