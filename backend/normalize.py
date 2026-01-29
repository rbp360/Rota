import pandas as pd
import openpyxl
from backend.database import SessionLocal, Staff, Schedule, Setting, engine, Base
from sqlalchemy.orm import Session
import os

EXCEL_PATH = r"c:\Users\rob_b\Rota\GV cover and staff absence.xlsx"

def normalize_data():
    db = SessionLocal()
    try:
        # Clear existing data to avoid duplicates
        db.query(Schedule).delete()
        db.query(Staff).delete()
        db.commit()

        print(f"Loading workbook: {EXCEL_PATH}")
        xl = pd.ExcelFile(EXCEL_PATH)
        sheet_names = xl.sheet_names
        
        # We assume sheets representing people have specific structures
        # Based on user: EY, TB, CCA are special columns.
        
        # Specific profiles from notes.txt
        teacher_profiles = {
            "Daryl": "Music teacher",
            "Jake": "Assistant that works throughout school",
            "Becky": "Drama teacher who teaches whole school",
            "Billy": "PE teacher who teaches whole school",
            "Retno": "Pre-nursery teacher",
            "Jacinta": "Nursery teacher",
            "Faye": "Predominantly used for covering",
            "Ginny": "Assistant who works with different classes and students",
            "Claire": "Head (used for cover), tab is 'ME'",
            "Ben": "Forest school teacher who teaches whole classes"
        }

        days_list = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        
        for name in sheet_names:
            # Updated ignore list: Added non-staff technical tabs
            name_lower = name.lower().replace(" ", "")
            ignore_list = [
                'instructions', 'summary', 'record', 'absencerecord', 
                'sheet3', 'sheet1', 'tb1', 'ey', 'cca', 'y56eal'
            ]
            if name_lower in ignore_list or name_lower.startswith('sheet'):
                continue
            
            # Map technical names to people
            staff_name = name
            if name == "ME": staff_name = "Claire"
            if name.lower() == "pre nursery": staff_name = "Retno"
            
            print(f"Normalizing: {staff_name}")
            
            # Initialize openpyxl sheet correctly
            wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True, read_only=True)
            sheet = wb[name]
            
            # 1. Staff Setup
            specialists = ["Daryl", "Becky", "Billy", "Jinny", "Ginny", "Ben", "Faye", "Claire", "Jake"]
            staff = db.query(Staff).filter(Staff.name == staff_name).first()
            if not staff:
                staff = Staff(
                    name=staff_name,
                    role="Teacher" if "Assistant" not in teacher_profiles.get(staff_name, "") else "TA",
                    profile=teacher_profiles.get(staff_name, ""),
                    is_priority=(staff_name == "Claire"),
                    is_specialist=(staff_name in specialists),
                    is_active=True
                )
                db.add(staff)
                db.flush()

            # 2. Schedule Parsing
            day_cols = {}
            header_row_idx = 0
            
            # Scans first 10 rows to find WHERE the days are mentioned
            for r_idx, row in enumerate(sheet.iter_rows(max_row=10, values_only=True)):
                found_in_row = False
                for idx, val in enumerate(row):
                    if val and str(val).strip() in days_list:
                        day_cols[str(val).strip()] = idx + 1
                        found_in_row = True
                if found_in_row:
                    header_row_idx = r_idx + 1
                    break
            
            if not day_cols:
                print(f"Warning: No day headers found for {staff_name}, using default.")
                day_cols = {d: i+2 for i, d in enumerate(days_list)}
                header_row_idx = 1

            # Get rows starting AFTER the header
            rows = list(sheet.iter_rows(min_row=header_row_idx + 1, max_row=header_row_idx + 10, values_only=True))
            
            for p_idx in range(1, 7): # Periods 1-6
                if p_idx > len(rows):
                    continue
                row_data = rows[p_idx-1]
                
                for day, col in day_cols.items():
                    # Calculate value accurately
                    raw_val = row_data[col-1] if col <= len(row_data) else None
                    val = str(raw_val).strip() if raw_val is not None else ""
                    
                    is_free = False
                    # A cell is free ONLY if it is truly empty or says 'free'
                    if not val or val.lower() in ['none', 'nan', 'free', 'available']:
                        is_free = True
                    
                    db.add(Schedule(
                        staff_id=staff.id,
                        day_of_week=day,
                        period=p_idx,
                        activity=val,
                        is_free=is_free
                    ))
        
        db.commit()
        print("Normalization complete.")
        
    except Exception as e:
        print(f"Error during normalization: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    normalize_data()
