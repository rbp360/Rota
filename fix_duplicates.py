import sqlite3
import pandas as pd

conn = sqlite3.connect('rota.db')
cursor = conn.cursor()

# Find duplicate absences for the same person and same date
print("Checking for duplicate absences...")
cursor.execute("""
    SELECT staff_id, date, COUNT(*) as cnt
    FROM absences
    GROUP BY staff_id, date
    HAVING cnt > 1
""")
dups = cursor.fetchall()

for staff_id, date, cnt in dups:
    print(f"Found {cnt} duplicates for staff {staff_id} on {date}")
    # Get all absence IDs for this combination
    cursor.execute("SELECT id FROM absences WHERE staff_id = ? AND date = ? ORDER BY id ASC", (staff_id, date))
    ids = [row[0] for row in cursor.fetchall()]
    
    keep_id = ids[0]
    to_merge = ids[1:]
    
    print(f"Keeping ID {keep_id}, merging {to_merge}")
    
    # Update covers to point to the kept ID
    for old_id in to_merge:
        cursor.execute("UPDATE covers SET absence_id = ? WHERE absence_id = ?", (keep_id, old_id))
        print(f"Updated covers for old absence {old_id}")
    
    # Delete the old absences
    for old_id in to_merge:
        cursor.execute("DELETE FROM absences WHERE id = ?", (old_id,))
        print(f"Deleted old absence {old_id}")

conn.commit()
print("Deduplication complete.")

# Verify final state
print("\nFinal State - Absences:")
cursor.execute("SELECT a.id, s.name, a.date FROM absences a JOIN staff s ON a.staff_id = s.id")
[print(row) for row in cursor.fetchall()]

print("\nFinal State - Covers:")
cursor.execute("SELECT c.id, c.absence_id, s.name as covering_staff, c.period FROM covers c JOIN staff s ON c.covering_staff_id = s.id")
[print(row) for row in cursor.fetchall()]

conn.close()
