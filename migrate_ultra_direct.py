import os
import json
import time

# 🆘 STEP 0: EXPLICITLY RE-FIX THE PEM KEY (Mathematical Repair)
JSON_PATH = "rotaai-49847-d923810f254e.json"

def fix_json_key():
    with open(JSON_PATH) as f:
        data = json.load(f)
    
    pk = data.get("private_key", "")
    # Remove literal \n and fix spacing
    pk = pk.replace("\\n", "\n")
    # Ensure it's clean (standard PEM format)
    if "-----BEGIN PRIVATE KEY-----" not in pk:
        return None
    
    data["private_key"] = pk
    return data

def migrate():
    print("--- FIRESTORE ULTRA-DIRECT SYNC ---")
    
    try:
        from google.cloud import firestore
        from google.oauth2 import service_account
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        # 1. Load and Fix the Key
        fixed_data = fix_json_key()
        if not fixed_data:
            print("Error: Private key format is unreadable.")
            return

        # 2. CREATE CLIENT INDEPENDENT OF SYSTEM SETTINGS
        # This completely ignores "Application Default Credentials"
        creds = service_account.Credentials.from_service_account_info(fixed_data)
        db = firestore.Client(project=fixed_data["project_id"], credentials=creds)
        
        print(f"Connected to {fixed_data['project_id']} successfully.")
    except Exception as e:
        print(f"Connection failed: {e}")
        return

    # 3. Load local data
    DB_PATH = os.path.join("data_archive", "rota.db")
    try:
        from backend.database import Staff, Schedule, Absence, Cover
        engine = create_engine(f"sqlite:///./{DB_PATH}")
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
    except Exception as e:
        print(f"Local DB Error: {e}")
        return

    staff_mems = session.query(Staff).all()
    print(f"Transferring {len(staff_mems)} staff profiles...")

    for i, s in enumerate(staff_mems):
        try:
            print(f"[{i+1}/{len(staff_mems)}] {s.name}...", end=" ", flush=True)
            
            staff_ref = db.collection("staff").document(str(s.id))
            staff_ref.set({
                "name": s.name,
                "role": s.role,
                "profile": s.profile,
                "is_active": s.is_active,
                "is_priority": s.is_priority,
                "is_specialist": s.is_specialist,
                "can_cover_periods": s.can_cover_periods
            })

            # Timetables
            schedules = session.query(Schedule).filter(Schedule.staff_id == s.id).all()
            batch = db.batch()
            for sch in schedules:
                doc_id = f"{sch.day_of_week}_{sch.period}"
                batch.set(staff_ref.collection("schedules").document(doc_id), {
                    "day_of_week": sch.day_of_week,
                    "period": sch.period,
                    "activity": sch.activity,
                    "is_free": sch.is_free
                })
            batch.commit()
            print("Done.")
            
        except Exception as e:
            print(f"Error: {e}")
            if "invalid_grant" in str(e):
                print("\nAUTH ERROR: JWT Signature rejected.")
                print("If your clock is right, the JSON file might have been revoked.")
                return

    print("\n✅ ALL DATA SYNCED!")

if __name__ == "__main__":
    migrate()
