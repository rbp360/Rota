try:
    import os
    if not os.path.exists("temp_rota.xlsx"):
        print("ERROR: temp_rota.xlsx does not exist! Copying it now...")
        import shutil
        shutil.copy("GV cover and staff absence.xlsx", "temp_rota.xlsx")
        
    from backend.database import engine, Base, SessionLocal, Staff, Schedule
    from backend.normalize import normalize_data
    
    print("--- STARTING AUTO-FIX ---")
    print("Dropping tables...")
    Base.metadata.drop_all(bind=engine)
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Running normalization...")
    normalize_data()
    
    # Check results
    db = SessionLocal()
    staff_count = db.query(Staff).count()
    sched_count = db.query(Schedule).count()
    print(f"--- AUTO-FIX COMPLETE ---")
    print(f"Staff Count: {staff_count}")
    print(f"Schedule Count: {sched_count}")
    
except Exception as e:
    print(f"CRITICAL ERROR: {e}")
    import traceback
    traceback.print_exc()
