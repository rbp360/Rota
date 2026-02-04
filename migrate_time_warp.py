import os
import json
import time
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 🕒 THE TIME WARP FIX
# Your computer clock is about 25 minutes FAST compared to Google.
# We will "trick" the script into using the correct time.
TIME_OFFSET_SECONDS = - (25 * 60 + 30) # Subtract 25 mins and 30 seconds

original_time = time.time
def warped_time():
    return original_time() + TIME_OFFSET_SECONDS

time.time = warped_time # Monkeypatch time

# ---------------------------------------------------------

JSON_PATH = "rotaai-49847-d923810f254e.json"
DB_PATH = os.path.join("data_archive", "rota.db")

def connect_firestore():
    from google.cloud import firestore
    from google.oauth2 import service_account
    
    print(f"\n--- TIME-WARPED SYNC (Offset: {TIME_OFFSET_SECONDS}s) ---")
    print(f"System Time: {datetime.datetime.now()}")
    print(f"Warped Time used for Google: {datetime.datetime.fromtimestamp(time.time())}")
    
    try:
        with open(JSON_PATH) as f:
            info = json.load(f)
            project_id = info["project_id"]
            
        creds = service_account.Credentials.from_service_account_info(info)
        return firestore.Client(project=project_id, credentials=creds)
    except Exception as e:
        print(f"CRITICAL CONNECTION ERROR: {e}")
        return None

def migrate():
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
                "name": s.name, "role": s.role, "profile": s.profile,
                "is_priority": s.is_priority, "is_specialist": s.is_specialist,
                "is_active": s.is_active, "can_cover_periods": s.can_cover_periods,
                "calendar_url": s.calendar_url
            })

            schedules = session.query(Schedule).filter(Schedule.staff_id == s.id).all()
            for sch in schedules:
                doc_id = f"{sch.day_of_week}_{sch.period}"
                staff_ref.collection("schedules").document(doc_id).set({
                    "day_of_week": sch.day_of_week, "period": sch.period,
                    "activity": sch.activity, "is_free": sch.is_free
                })
            
            print(f"  [{i+1}/{len(staff_mems)}] ✅ {s.name}")
        except Exception as e:
            print(f"  ❌ FAIL on {s.name}: {e}")
            return

    print("\n🎉 SYNC COMPLETE!")

if __name__ == "__main__":
    migrate()
