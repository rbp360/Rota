
from backend.database import SessionLocal, Staff
import sys

def list_all_staff():
    db = SessionLocal()
    try:
        staff_list = db.query(Staff).order_by(Staff.name).all()
        print(f"Total Staff Found: {len(staff_list)}")
        print("-" * 30)
        for s in staff_list:
            print(f"{s.name}")
        print("-" * 30)
    finally:
        db.close()

if __name__ == "__main__":
    list_all_staff()
