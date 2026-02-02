import os
import sqlite3
import requests
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 1. CONFIGURE YOUR URL HERE
# Change this to your actual Vercel app URL (e.g., https://my-app.vercel.app)
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
    bundle = []
    
    for s in staff_members:
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
        
        # Add schedules
        schedules = session.query(Schedule).filter(Schedule.staff_id == s.id).all()
        for sch in schedules:
            staff_data["schedules"].append({
                "day_of_week": sch.day_of_week,
                "period": sch.period,
                "activity": sch.activity,
                "is_free": sch.is_free
            })
        bundle.append(staff_data)

    print(f"Sending {len(bundle)} teachers to the website...")
    try:
        response = requests.post(f"{TARGET_URL}/api/import-staff", json=bundle)
        if response.status_code == 200:
            print(f"SUCCESS! Server response: {response.json()}")
        else:
            print(f"FAILED. Code: {response.status_code}, Body: {response.text}")
    except Exception as e:
        print(f"ERROR connecting to website: {e}")

if __name__ == "__main__":
    if "your-app-url" in TARGET_URL:
        print("ERROR: Please edit push_to_cloud.py and put your real Vercel URL in TARGET_URL.")
    else:
        migrate_via_bridge()
