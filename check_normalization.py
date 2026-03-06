import sqlite3
import os

def check():
    if not os.path.exists('rota.db'):
        print("rota.db not found in root")
        return
        
    conn = sqlite3.connect('rota.db')
    cursor = conn.cursor()
    
    # Check Alex
    cursor.execute("SELECT id, name FROM staff WHERE name LIKE '%Alex%'")
    alex = cursor.fetchone()
    if alex:
        print(f"Found Alex: ID={alex[0]}, Name={alex[1]}")
        cursor.execute("SELECT day_of_week, period, activity, is_free FROM schedules WHERE staff_id = ? AND period = 1", (alex[0],))
        for row in cursor.fetchall():
            print(f"  {row[0]} P1: {row[1]} (Free: {row[2]})")
    else:
        print("Alex not found")
        
    # Check Amanda
    cursor.execute("SELECT id, name FROM staff WHERE name LIKE '%Amanda%'")
    amanda = cursor.fetchone()
    if amanda:
        print(f"Found Amanda: ID={amanda[0]}, Name={amanda[1]}")
        cursor.execute("SELECT day_of_week, period, activity, is_free FROM schedules WHERE staff_id = ? AND period = 1", (amanda[0],))
        for row in cursor.fetchall():
             print(f"  {row[0]} P1: {row[1]} (Free: {row[2]})")
    else:
        print("Amanda not found")
        
    conn.close()

if __name__ == "__main__":
    check()
