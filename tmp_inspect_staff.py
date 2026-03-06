import os
import sys

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.database_firestore import FirestoreDB

def inspect_staff(name):
    print(f"\n--- Checking {name} ---")
    print(f"Fetching staff member '{name}'...")
    staff = FirestoreDB.get_staff_member(name=name)
    print(f"Result: {staff}")
    if not staff:
        print(f"Staff '{name}' not found!")
        return
    
    print(f"ID: {staff['id']}")
    print(f"Role: {staff.get('role')}")
    
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    for day in days:
        print(f"\n  Day: {day}")
        schedules = FirestoreDB.get_schedules(staff['id'], day=day)
        # Sort by period
        schedules.sort(key=lambda x: x.get('period', 0))
        for sch in schedules:
            if sch.get('period') == 1:
                print(f"    P1: {sch.get('activity')} (is_free={sch.get('is_free')})")

if __name__ == "__main__":
    # Check if FIREBASE_KEY_HEX is set, or if we need to use the local json file
    # For this environment, we might need to set the env var from the file
    json_path = "rotaai-49847-d923810f254e.json"
    if os.path.exists(json_path):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.abspath(json_path)
    
    inspect_staff("Alex")
    inspect_staff("Amanda")
