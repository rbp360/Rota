import os
import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database import Base, Staff, Schedule, Absence, Cover
from backend.database_firestore import db, firestore

# Setup SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:///./rota.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

def migrate():
    print("Starting migration to Firestore...")

    # 1. Migrate Staff and their Schedules
    staff_members = session.query(Staff).all()
    print(f"Migrating {len(staff_members)} staff members...")
    
    for s in staff_members:
        staff_id = str(s.id)
        staff_ref = db.collection("staff").document(staff_id)
        staff_ref.set({
            "name": s.name,
            "role": s.role,
            "profile": s.profile,
            "is_priority": s.is_priority,
            "is_specialist": s.is_specialist,
            "is_active": s.is_active,
            "can_cover_periods": s.can_cover_periods,
            "calendar_url": s.calendar_url
        })

        # Subcollection for schedules
        schedules = session.query(Schedule).filter(Schedule.staff_id == s.id).all()
        for sch in schedules:
            # Document ID like "Monday_1"
            sched_ref = staff_ref.collection("schedules").document(f"{sch.day_of_week}_{sch.period}")
            sched_ref.set({
                "day_of_week": sch.day_of_week,
                "period": sch.period,
                "activity": sch.activity,
                "location": sch.location,
                "is_free": sch.is_free
            })

    # 2. Migrate Absences and their Covers
    absences = session.query(Absence).all()
    print(f"Migrating {len(absences)} absences...")
    
    for a in absences:
        absence_id = str(a.id)
        abs_ref = db.collection("absences").document(absence_id)
        abs_ref.set({
            "staff_id": str(a.staff_id),
            "staff_name": a.staff.name,
            "date": a.date.isoformat(),
            "start_period": a.start_period,
            "end_period": a.end_period,
            "reason": a.reason
        })

        # Subcollection for covers
        covers = session.query(Cover).filter(Cover.absence_id == a.id).all()
        for c in covers:
            cover_ref = abs_ref.collection("covers").document(str(c.period))
            cover_ref.set({
                "covering_staff_id": str(c.covering_staff_id),
                "covering_staff_name": c.covering_staff.name,
                "period": c.period,
                "status": c.status,
                "reason_for_selection": c.reason_for_selection
            })

    print("Migration complete!")

if __name__ == "__main__":
    migrate()
