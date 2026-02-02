from backend.database import SessionLocal, Staff, Schedule
db = SessionLocal()

try:
    with open("audit_result.txt", "w") as f:
        staff = db.query(Staff).all()
        f.write(f"Total Staff: {len(staff)}\n")
        for s in staff:
            f.write(f"{s.name} - Role: {s.role}, CanCoverP: {s.can_cover_periods}\n")
        
        schedules = db.query(Schedule).filter(Schedule.period.in_([0, 9, 10])).all()
        f.write(f"Total Duties Found: {len(schedules)}\n")
        if schedules:
            f.write("Sample Duties:\n")
            for sch in schedules[:10]:
                 f.write(f"  {sch.staff.name} P{sch.period} - {sch.activity}\n")
except Exception as e:
    with open("audit_error.txt", "w") as f:
        f.write(str(e))
