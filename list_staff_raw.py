
import sqlite3

def list_staff_raw():
    try:
        conn = sqlite3.connect(r"c:\Users\rob_b\Rota\rota.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM staff ORDER BY name")
        rows = cursor.fetchall()
        print(f"Total: {len(rows)}")
        for r in rows:
            print(r[0])
        conn.close()
    except Exception as e:
        print(e)

if __name__ == "__main__":
    list_staff_raw()
