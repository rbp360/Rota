import sys
import os
from sqlalchemy import func
from .database import Staff, Schedule, Absence, Cover

def clean_staff_name(name):
    if not name: return ""
    n = str(name).strip()
    
    # GLOBAL IGNORE LIST
    IGNORED = [
        "TBC", "External", "Coach", "Room", "Music Room", "Hall",
        "Gym", "Pitch", "Court", "Pool", "Library", "PRE NURSERY", "PRE NUSERY", "Outside Prov.",
        "**", "gate", "locked", "at", "8.30", "Mr", "1", "Calire", "?"
    ]
    if any(i.lower() in n.lower() for i in IGNORED):
        return None

    import re
    # Remove "K.", "Kun ", "K " prefixes
    n = re.sub(r'^(k\.|kun\s|k\s)', '', n, flags=re.IGNORECASE).strip()
    # Remove brackets and content e.g. "Charlotte (Thu)" -> "Charlotte"
    n = n.split('(')[0].strip()
    
    # Common Mappings
    nl = n.lower()
    
    # Fix Typos / Combine Duplicates
    if "jactina" in nl: return "Jacinta"
    if "nokkeaw" in nl: return "Nokkaew"
    if "nick" in nl and ("c" in nl or nl == "nick"): return "Nick C" # Matches "Nick C", "Nick. C", "Nick"
    
    if nl == "darryl": return "Daryl"
    if nl == "ginny": return "Jinny"
    if nl == "jinny": return "Jinny" 
    if nl == "janel": return "Janel"
    
    return n

def run_merge_in_session(db):
    all_staff = db.query(Staff).all()
    logs = []
    
    # 1. Group staff by canonical name
    by_canon = {}
    for s in all_staff:
        canon = clean_staff_name(s.name)
        if not canon:
            logs.append(f"Deleting ignored staff: {s.name}")
            db.query(Schedule).filter(Schedule.staff_id == s.id).delete()
            db.query(Absence).filter(Absence.staff_id == s.id).delete()
            db.query(Cover).filter(Cover.covering_staff_id == s.id).delete()
            db.delete(s)
            continue
        
        if canon not in by_canon:
            by_canon[canon] = []
        by_canon[canon].append(s)

    # 2. Process each canonical group
    for canon, staff_list in by_canon.items():
        # Pick primary: prefer one that already has the exact canonical name
        primary = next((s for s in staff_list if s.name == canon), None)
        
        # If none match exactly, pick first and rename
        if not primary:
            primary = staff_list[0]
            primary.name = canon
            db.flush() # Ensure rename is applied before merging others
            logs.append(f"Renamed {primary.id} to canonical {canon}")

        # Merge others into primary
        for s in staff_list:
            if s.id == primary.id:
                continue
            
            logs.append(f"Merging: {s.name} (ID {s.id}) into {primary.name}")
            db.query(Schedule).filter(Schedule.staff_id == s.id).update({Schedule.staff_id: primary.id})
            db.query(Absence).filter(Absence.staff_id == s.id).update({Absence.staff_id: primary.id})
            db.query(Cover).filter(Cover.covering_staff_id == s.id).update({Cover.covering_staff_id: primary.id})
            db.delete(s)
    
    db.commit()
    return logs

if __name__ == "__main__":
    from .database import SessionLocal
    db = SessionLocal()
    try:
        results = run_merge_in_session(db)
        for r in results: print(r)
    finally:
        db.close()
