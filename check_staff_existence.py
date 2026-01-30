
from backend.database import SessionLocal, Staff
db = SessionLocal()
names = ["Jayme", "Amanda", "Rosie"]
for name in names:
    staff = db.query(Staff).filter(Staff.name.ilike(f"%{name}%")).all()
    print(f"Searching for {name}: {[s.name for s in staff]}")
db.close()
