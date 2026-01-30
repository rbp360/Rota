import sqlite3
import os

DB_PATH = r"c:\Users\rob_b\Rota\rota.db"

def check_staff():
    if not os.path.exists(DB_PATH):
        print(f"DB not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, name FROM staff ORDER BY name")
    rows = cursor.fetchall()
    
    for row in rows:
        print(f"ID: {row[0]}, Name: {row[1]}")
    
    conn.close()

if __name__ == "__main__":
    check_staff()
