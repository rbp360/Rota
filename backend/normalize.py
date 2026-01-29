import pandas as pd
import openpyxl
from backend.database import SessionLocal, Staff, Schedule, Setting, engine, Base
from sqlalchemy.orm import Session
import os

EXCEL_PATH = r"c:\Users\rob_b\Rota\temp_rota.xlsx"

def normalize_data():
    db = SessionLocal()
    try:
        # Clear existing data
        db.query(Schedule).delete()
        db.query(Staff).delete()
        db.commit()

        days_list = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        
        print(f"Loading workbook: {EXCEL_PATH}...")
        wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)
        sheet_names = wb.sheetnames

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
        
        for name in sheet_names:
            name_lower = name.lower().replace(" ", "")
            ignore_list = [
                'instructions', 'summary', 'record', 'absencerecord', 
                'sheet3', 'sheet1', 'tb1', 'ey', 'cca', 'y56eal'
            ]
            if name_lower in ignore_list or name_lower.startswith('sheet'):
                continue
            
            staff_name = name
            if name == "ME": staff_name = "Claire"
            if name.lower() == "pre nursery": staff_name = "Retno"
            
            print(f"--- Normalizing: {staff_name} ---")
            sheet = wb[name]
            
            # Identify specialists (non-form teachers)
            specialists_list = [
                "Daryl", "Becky", "Billy", "Jinny", "Ginny", "Ben", "Faye", 
                "Claire", "Jake", "Retno", "Jacinta", "Sunny"
            ]
            
            staff = db.query(Staff).filter(Staff.name == staff_name).first()
            if not staff:
                staff = Staff(
                    name=staff_name,
                    role="Teacher" if "Assistant" not in teacher_profiles.get(staff_name, "") else "TA",
                    profile=teacher_profiles.get(staff_name, ""),
                    is_priority=(staff_name == "Claire"),
                    is_specialist=(staff_name in specialists_list or staff_name in teacher_profiles),
                    is_active=True
                )
                db.add(staff)
                db.flush()

            # Find day columns - scan first 20 rows
            day_cols = {}
            header_row_idx = 0
            for r_idx, row in enumerate(sheet.iter_rows(max_row=20, values_only=True)):
                found_in_row = False
                for c_idx, val in enumerate(row):
                    if not val: continue
                    val_str = str(val).strip().lower()
                    for d in days_list:
                        if d.lower() in val_str:
                            day_cols[d] = c_idx + 1
                            found_in_row = True
                if found_in_row and len(day_cols) >= 3:
                    header_row_idx = r_idx + 1
                    break
            
            if not day_cols:
                day_cols = {d: i+2 for i, d in enumerate(days_list)}
                header_row_idx = 1
            
            # Parse periods 1-6
            # We look for rows that likely contain period data
            p_rows = list(sheet.iter_rows(min_row=header_row_idx + 1, max_row=header_row_idx + 15, values_only=True))
            
            for p_num in range(1, 7): # P1-P6
                row_data = p_rows[p_num-1] if (p_num-1) < len(p_rows) else [None]*50
                
                for day, col in day_cols.items():
                    raw_val = row_data[col-1] if col <= len(row_data) else None
                    val = str(raw_val).strip() if raw_val is not None else ""
                    
                    is_available = False
                    
                    # Debug print for known busy form teachers (e.g. Jill/Charlotte)
                    if staff_name in ["Jill", "Charlotte"] and day == "Thursday" and p_num == 1:
                        print(f"DEBUG {staff_name} Thu P1: '{val}'")

                    # STRICTER CHECK:
                    # A cell is only free if it's explicitly empty or key 'free' words.
                    # Anything else (dates, room numbers, subjects, form names like '4B') counts as BUSY.
                    clean_val = val.lower().replace(" ", "")
                    free_keywords = ['none', 'nan', 'free', 'available', '0', '0.0']
                    
                    if not val or clean_val in free_keywords:
                        is_available = True
                    
                    db.add(Schedule(
                        staff_id=staff.id,
                        day_of_week=day,
                        period=p_num,
                        activity=val,
                        is_free=is_available
                    ))
        
        db.commit()
        
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
