import os
import sqlite3
import requests
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 1. CONFIGURE YOUR URL HERE
TARGET_URL = "https://rota-47dp.onrender.com" 

def migrate_via_bridge():
    print(f"Connecting to local SQLite...")
    db_path = os.path.join("data_archive", "rota.db")
    if not os.path.exists(db_path):
        print("Local DB not found.")
        return

    from backend.database import Staff, Schedule
    engine = create_engine(f"sqlite:///./{db_path}")
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    print("Bundling data...")
    staff_members = session.query(Staff).all()
    
    # We will send teachers in chunks to avoid Render 502 timeouts
    CHUNK_SIZE = 5
    total_imported = 0

    for i in range(0, len(staff_members), CHUNK_SIZE):
        chunk = staff_members[i:i + CHUNK_SIZE]
        bundle = []
        
        for s in chunk:
            staff_data = {
                "id": s.id,
                "name": s.name,
                "role": s.role,
                "profile": s.profile,
                "is_priority": s.is_priority,
                "is_specialist": s.is_specialist,
                "is_active": s.is_active,
                "can_cover_periods": s.can_cover_periods,
                "calendar_url": s.calendar_url,
                "schedules": []
            }
            
            schedules = session.query(Schedule).filter(Schedule.staff_id == s.id).all()
            for sch in schedules:
                staff_data["schedules"].append({
                    "day_of_week": sch.day_of_week,
                    "period": sch.period,
                    "activity": sch.activity,
                    "is_free": sch.is_free
                })
            bundle.append(staff_data)

        print(f"Sending chunk ({i}-{i+len(bundle)}) to the website...")
        try:
            # Increase timeout to 120s just in case
            response = requests.post(f"{TARGET_URL}/api/import-staff", json=bundle, timeout=120)
            if response.status_code == 200:
                print(f"  CHUNK SUCCESS! {response.json().get('imported', 0)} teachers imported.")
                total_imported += response.json().get('imported', 0)
            else:
                print(f"  CHUNK FAILED. Code: {response.status_code}, Body: {response.text}")
        except Exception as e:
            print(f"  ERROR connecting to website: {e}")

    print(f"\nCOMPLETED. Total teachers imported: {total_imported}/{len(staff_members)}")

if __name__ == "__main__":
    migrate_via_bridge()
