import sqlite3

conn = sqlite3.connect('rota.db')
cursor = conn.cursor()

print("Absences:")
cursor.execute("SELECT a.id, s.name, a.date FROM absences a JOIN staff s ON a.staff_id = s.id")
rows = cursor.fetchall()
for row in rows:
    print(row)

print("\nCovers:")
cursor.execute("SELECT c.id, c.absence_id, s.name as covering_staff, c.period FROM covers c JOIN staff s ON c.covering_staff_id = s.id")
rows = cursor.fetchall()
for row in rows:
    print(row)

conn.close()
