import os
import json
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 1. SETUP
JSON_PATH = "rotaai-49847-firebase-adminsdk-fbsvc-59f11aeb6b.json"
DB_PATH = os.path.join("data_archive", "rota.db")
RENDER_URL = "https://rota-47dp.onrender.com" # The actual Render URL

def migrate_via_api():
    print(f"--- API-BASED MIGRATION (Target: {RENDER_URL}) ---")
    import requests
    
    try:
        from backend.database import Staff, Schedule, Absence, Cover
        engine = create_engine(f"sqlite:///./{DB_PATH}")
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
    except Exception as e:
        print(f"Local DB Error: {e}")
        return

    staff_members = session.query(Staff).all()
    print(f"Found {len(staff_members)} staff members locally.")

    total_success = 0
    for i, s in enumerate(staff_members):
        print(f"[{i+1}/{len(staff_members)}] Sending {s.name}...", end=" ", flush=True)
        
        # Prepare data for THIS staff member
        schedules = session.query(Schedule).filter(Schedule.staff_id == s.id).all()
        data = [{
            "id": s.id,
            "name": s.name,
            "role": s.role,
            "profile": s.profile,
            "is_priority": s.is_priority,
            "is_specialist": s.is_specialist,
            "is_active": s.is_active,
            "can_cover_periods": s.can_cover_periods,
            "calendar_url": s.calendar_url,
            "schedules": [
                {
                    "day_of_week": sch.day_of_week,
                    "period": sch.period,
                    "activity": sch.activity,
                    "is_free": sch.is_free
                } for sch in schedules
            ]
        }]

        # Send to Render with EXTREME patience
        success = False
        for attempt in range(3):
            try:
                # We use a 120 second timeout per teacher
                resp = requests.post(
                    f"{RENDER_URL}/api/import-staff", 
                    json=data, 
                    timeout=120
                )
                if resp.status_code == 200:
                    print("✅")
                    total_success += 1
                    success = True
                    break
                else:
                    print(f"❌ (Status {resp.status_code})")
                    break
            except Exception as e:
                if attempt < 2:
                    print(f" (Retrying {attempt+1}...)", end="", flush=True)
                    time.sleep(5)
                else:
                    print(f" ❌ (Timeout/Error: {e})")

    print(f"\nMigration complete. {total_success}/{len(staff_members)} staff uploaded.")
    print("Check your frontend now!")

if __name__ == "__main__":
    migrate_via_api()
