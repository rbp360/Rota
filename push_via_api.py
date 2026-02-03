import os
import sqlite3
import requests
import json
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 1. CONFIGURATION
# Using the production URL
RENDER_URL = "https://rota-47dp.onrender.com/api/import-staff"

def migrate_via_api():
    print(f"Starting SLOW & STEADY API-based migration to: {RENDER_URL}")

    db_path = os.path.join("data_archive", "rota.db")
    if not os.path.exists(db_path):
        print(f"Local SQLite DB not found at {db_path}")
        return

    # Import local models
    try:
        from backend.database import Staff, Schedule
    except ImportError:
        print("Backend models not found. Run from the Rota root folder.")
        return

    engine = create_engine(f"sqlite:///./{db_path}")
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    staff_members = session.query(Staff).all()
    print(f"Found {len(staff_members)} staff members. Processing ONE BY ONE to prevent timeouts...")

    total_success = 0
    
    # PROCESS ONE BY ONE
    for i, s in enumerate(staff_members):
        payload = []
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

        # Fetch schedules
        schedules = session.query(Schedule).filter(Schedule.staff_id == s.id).all()
        for sch in schedules:
            staff_data["schedules"].append({
                "day_of_week": sch.day_of_week,
                "period": sch.period,
                "activity": sch.activity,
                "is_free": sch.is_free
            })
        
        payload.append(staff_data)

        print(f"[{i+1}/{len(staff_members)}] Uploading {s.name}...")
        
        # We give it a huge timeout (120s) for just one person
        # and we retry up to 3 times
        success = False
        for attempt in range(3):
            try:
                response = requests.post(RENDER_URL, json=payload, timeout=120)
                if response.status_code == 200:
                    result = response.json()
                    imported = result.get('imported', 0)
                    if imported > 0:
                        total_success += 1
                        print(f"  ✅ [SUCCESS] Imported {s.name}")
                        success = True
                        break
                    else:
                        print(f"  ⚠️ [WARNING] Server returned success but 0 imported for {s.name}")
                else:
                    # Capture the first 200 chars of error for debugging
                    err_msg = response.text[:200]
                    print(f"  ❌ [ERROR] {response.status_code} for {s.name}: {err_msg}")
            except Exception as e:
                print(f"  ⚠️ Attempt {attempt+1} failed ({e}). Retrying...")
                time.sleep(2)
        
        if not success:
            print(f"  ❌ GIVING UP on {s.name}")

    print(f"\n✅ FINISHED. Successfully synced {total_success} staff members.")
    print("Refresh your browser to check the data.")

if __name__ == "__main__":
    migrate_via_api()
