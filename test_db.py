
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from backend.database import SessionLocal, Staff
    db = SessionLocal()
    staff = db.query(Staff).all()
    print(f"Success! Found {len(staff)} staff members.")
    for s in staff[:3]:
        print(f"- {s.name} ({s.role})")
    db.close()
except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
