
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.database import SessionLocal, Staff, Schedule

def check_duties_and_ccas():
    db = SessionLocal()
    
    # Check if there are ANY schedules for periods 0, 9, 10, 11, 13
    special_periods = [0, 9, 10, 11, 13]
    count = db.query(Schedule).filter(Schedule.period.in_(special_periods)).count()
    print(f"Total special period entries (0, 9, 10, 11, 13): {count}")
    
    if count > 0:
        # Show first 10
        samples = db.query(Schedule).filter(Schedule.period.in_(special_periods)).limit(10).all()
        for s in samples:
            staff = db.query(Staff).get(s.staff_id)
            print(f"- Staff: {staff.name}, Day: {s.day_of_week}, Period: {s.period}, Activity: {s.activity}")
    else:
        # Check all periods for any staff to see what we have
        print("\nChecking all periods for a sample staff member (Daryl):")
        daryl = db.query(Staff).filter(Staff.name == 'Daryl').first()
        if daryl:
            schedules = db.query(Schedule).filter(Schedule.staff_id == daryl.id).all()
            for s in sorted(schedules, key=lambda x: (x.day_of_week, x.period)):
                print(f"  - {s.day_of_week} P{s.period}: {s.activity} (Free: {s.is_free})")
        else:
            print("Daryl not found.")
            
    db.close()

if __name__ == "__main__":
    check_duties_and_ccas()
