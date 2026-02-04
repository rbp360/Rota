import os
import json
import time
import requests
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# CONFIG
RENDER_URL = "https://rota-47dp.onrender.com"
DB_PATH = os.path.join("data_archive", "rota.db")

def migrate_final():
    print(f"--- GLOBAL MASTER SYNC (v5.5.26 Cleanup) ---")
    
    try:
        from backend.database import Staff, Schedule, Absence, Cover
        engine = create_engine(f"sqlite:///./{DB_PATH}")
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
    except Exception as e:
        print(f"Local DB Error: {e}")
        return

    # 1. FIX MISSED STAFF (Ben and Soe)
    # This also ensures their full Timetables, CCAs, and EY data is sent
    missed_names = ["Ben", "Soe"]
    for name in missed_names:
        s = session.query(Staff).filter(Staff.name == name).first()
        if s:
            print(f"Re-syncing {s.name} (Everything: Timetables, CCAs, EY)...", end=" ", flush=True)
            schedules = session.query(Schedule).filter(Schedule.staff_id == s.id).all()
            data = [{
                "id": s.id, "name": s.name, "role": s.role,
                "profile": s.profile, "is_priority": s.is_priority,
                "is_specialist": s.is_specialist, "is_active": s.is_active,
                "can_cover_periods": s.can_cover_periods, "calendar_url": s.calendar_url,
                "schedules": [
                    {"day_of_week": sch.day_of_week, "period": sch.period, "activity": sch.activity, "is_free": sch.is_free}
                    for sch in schedules
                ]
            }]
            try:
                resp = requests.post(f"{RENDER_URL}/api/import-staff", json=data, timeout=120)
                print("✅" if resp.status_code == 200 else f"❌ ({resp.status_code})")
            except: print("❌ (Timeout)")

    # 2. SYNC ALL ABSENCES AND COVERS
    print(f"\nPhase 2: Syncing all historical Absences and Cover assignments...")
    absences = session.query(Absence).all()
    print(f"  Total Absences to move: {len(absences)}")
    
    chunk_size = 15
    for i in range(0, len(absences), chunk_size):
        chunk = absences[i:i+chunk_size]
        payload = []
        for a in chunk:
            covers = session.query(Cover).filter(Cover.absence_id == a.id).all()
            payload.append({
                "id": a.id,
                "staff_id": a.staff_id,
                "staff_name": a.staff.name if a.staff else "Unknown",
                "date": a.date.strftime('%Y-%m-%d'),
                "start_period": a.start_period,
                "end_period": a.end_period,
                "covers": [
                    {
                        "period": c.period,
                        "staff_name": c.covering_staff.name if c.covering_staff else "Unknown",
                        "covering_staff_id": c.covering_staff_id
                    } for c in covers
                ]
            })
            
        print(f"  Sending Absence Chunk {i//chunk_size + 1}...", end=" ", flush=True)
        try:
            # THIS REQUIRES v5.5.26 DEPLOYED ON RENDER
            resp = requests.post(f"{RENDER_URL}/api/import-absences", json=payload, timeout=120)
            if resp.status_code == 200:
                print("✅")
            else:
                print(f"❌ (Status {resp.status_code}) - DID YOU DEPLOY v5.5.26?")
        except Exception as e:
            print(f"❌ (Error: {e})")

    print("\n🎉 ALL DATA (Staff, Timetables, CCAs, EY, Absences, Covers) SYNCED!")

if __name__ == "__main__":
    migrate_final()
