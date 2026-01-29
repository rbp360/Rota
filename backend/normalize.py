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
            
            # Explicitly force is_specialist to match the list exactly, else False (0)
            is_spec = (staff_name in specialists_list)

            staff = db.query(Staff).filter(Staff.name == staff_name).first()
            if not staff:
                staff = Staff(
                    name=staff_name,
                    role="Teacher" if "Assistant" not in teacher_profiles.get(staff_name, "") else "TA",
                    profile=teacher_profiles.get(staff_name, ""),
                    is_priority=(staff_name == "Claire"),
                    is_specialist=is_spec,
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
                        if d.lower() == val_str: # Exact match
                            day_cols[d] = c_idx + 1
                            found_in_row = True
                        elif d.lower() in val_str and len(val_str) < 15: # Partial match (e.g. "Monday 25th")
                            day_cols[d] = c_idx + 1
                            found_in_row = True
                if found_in_row and len(day_cols) >= 3:
                    header_row_idx = r_idx + 1
                    break
            
            if not day_cols:
                day_cols = {d: i+2 for i, d in enumerate(days_list)}
                header_row_idx = 1
            
            print(f"  Day Columns: {day_cols} (Header Row: {header_row_idx})")

            # Parse periods 1-8
            p_rows_map = {}
            for r_idx, row in enumerate(sheet.iter_rows(max_row=60, values_only=True)):
                # Check first 5 columns for period markers
                markers = [str(v).strip().lower() for v in row[:5] if v is not None]
                for p_num in range(1, 9):
                    if p_num in p_rows_map: continue
                    # Common markers: "1", "P1", "Period 1", "P.1"
                    possible = [str(p_num), f"p{p_num}", f"period {p_num}", f"p.{p_num}", f"per {p_num}"]
                    if any(m in markers for m in possible):
                        p_rows_map[p_num] = row
                        break
            
            for p_num in range(1, 9):
                row_data = p_rows_map.get(p_num)
                if row_data is None:
                    # Fallback
                    rows_cached = list(sheet.iter_rows(min_row=header_row_idx + 1, max_row=header_row_idx + 30, values_only=True))
                    row_data = rows_cached[p_num-1] if (p_num-1) < len(rows_cached) else [None]*50
                    print(f"    P{p_num} using fallback row")
                else:
                    print(f"    P{p_num} found marker row")

                for day, col in day_cols.items():
                    raw_val = row_data[col-1] if col <= len(row_data) else None
                    val = str(raw_val).strip() if raw_val is not None else ""
                    
                    is_available = False
                    clean_val = val.lower().replace(" ", "")
                    free_keywords = ['none', 'nan', 'free', 'available', '0', '0.0', '']
                    
                    if not clean_val or clean_val in free_keywords:
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
