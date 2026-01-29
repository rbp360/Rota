import sqlite3
import pandas as pd

conn = sqlite3.connect('rota.db')
print("Absences:")
df_absences = pd.read_sql_query("SELECT a.id, s.name, a.date FROM absences a JOIN staff s ON a.staff_id = s.id", conn)
print(df_absences)

print("\nCovers:")
df_covers = pd.read_sql_query("SELECT c.id, c.absence_id, s.name as covering_staff, c.period FROM covers c JOIN staff s ON c.covering_staff_id = s.id", conn)
print(df_covers)

conn.close()
