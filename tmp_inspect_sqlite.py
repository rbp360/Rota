import sqlite3
import os

db_path = os.path.join("data_archive", "rota.db")

def inspect_sqlite(name):
    print(f"\n--- SQLite: Checking {name} ---")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, name, role FROM staff WHERE name LIKE ?", (f"%{name}%",))
    staff = cursor.fetchone()
    if not staff:
        print(f"Staff '{name}' not found!")
        return
    
    print(f"ID: {staff['id']}, Name: {staff['name']}, Role: {staff['role']}")
    
    cursor.execute("SELECT day_of_week, period, activity, is_free FROM schedules WHERE staff_id = ? AND period = 1 ORDER BY day_of_week", (staff['id'],))
    schedules = cursor.fetchall()
    for sch in schedules:
        print(f"  {sch['day_of_week']} P1: {sch['activity']} (is_free={sch['is_free']})")
    
    conn.close()

if __name__ == "__main__":
    inspect_sqlite("Alex")
    inspect_sqlite("Amanda")
