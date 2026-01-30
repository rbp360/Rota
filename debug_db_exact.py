
import sqlite3
import binascii

def analyze_db():
    conn = sqlite3.connect(r"c:\Users\rob_b\Rota\rota.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM staff ORDER BY name")
    rows = cursor.fetchall()
    print(f"Total rows: {len(rows)}")
    print("-" * 40)
    for r in rows:
        sid, name = r
        # Print name in quotes to see trailing spaces, and look for duplicates
        print(f"ID: {sid:3d} | Name: '{name}'")
        
        # Check specific problematic ones
        if "jac" in name.lower() or "nok" in name.lower() or "nick" in name.lower():
            hex_val = binascii.hexlify(name.encode('utf-8')).decode('utf-8')
            print(f"    -> HEX: {hex_val}")
            
    conn.close()

if __name__ == "__main__":
    analyze_db()
