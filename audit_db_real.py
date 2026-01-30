
from backend.database import SessionLocal, Staff
import sys

def audit():
    db = SessionLocal()
    staff = db.query(Staff).all()
    names = sorted([s.name for s in staff])
    
    with open("final_staff_audit.txt", "w") as f:
        f.write("--- STAFF LIST FROM DB ---\n")
        for n in names:
            f.write(f"{n}\n")
    
    print("Audit written to final_staff_audit.txt")

if __name__ == "__main__":
    audit()
