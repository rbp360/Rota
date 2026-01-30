
from backend.database import SessionLocal, Staff
import os

def list_all_staff():
    print("Connecting to DB...")
    try:
        db = SessionLocal()
        staff_list = db.query(Staff).order_by(Staff.name).all()
        print(f"Total Staff Found: {len(staff_list)}")
        
        with open("staff_list_final.txt", "w") as f:
            for s in staff_list:
                f.write(f"{s.name}\n")
        print("Written to staff_list_final.txt")
        db.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_all_staff()
