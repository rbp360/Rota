
import sqlite3

def check_schema():
    try:
        conn = sqlite3.connect("rota.db")
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(staff)")
        columns = cursor.fetchall()
        print("Columns in 'staff' table:")
        found = False
        for col in columns:
            print(col)
            if col[1] == 'can_cover_periods':
                found = True
        
        if found:
            print("\nSUCCESS: 'can_cover_periods' column EXISTS.")
        else:
            print("\nFAILURE: 'can_cover_periods' column IS MISSING.")
        conn.close()
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    import sys
    sys.stdout = open("schema_check_result.txt", "w")
    check_schema()

