import sqlite3
import os

db_path = r"c:\Users\rob_b\Rota\rota.db"

def migrate():
    if not os.path.exists(db_path):
        print("DB not found, it will be created fresh during normalization.")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("PRAGMA table_info(staff)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if "is_specialist" not in columns:
            print("Adding is_specialist column...")
            cursor.execute("ALTER TABLE staff ADD COLUMN is_specialist BOOLEAN DEFAULT 0")
            conn.commit()
            print("Migration successful.")
        else:
            print("Column already exists.")
            
        conn.close()
    except Exception as e:
        print(f"Migration error: {e}")

if __name__ == "__main__":
    migrate()
