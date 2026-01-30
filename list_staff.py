import sqlite3
import os

DB_PATH = r"c:\Users\rob_b\Rota\rota.db"

def list_staff():
    if not os.path.exists(DB_PATH):
        print(f"DB not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM staff ORDER BY name")
    rows = cursor.fetchall()
    
    print(f"Total Staff: {len(rows)}")
    for row in rows:
        print(row[0])
    
    conn.close()

if __name__ == "__main__":
    list_staff()
