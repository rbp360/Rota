
import os
import sys

# Ensure backend is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.database import engine, Base

def reset():
    db_file = "rota.db"
    if os.path.exists(db_file):
        print(f"Deleting {db_file}...")
        try:
            os.remove(db_file)
            print("Deleted successfully.")
        except Exception as e:
            print(f"Failed to delete {db_file}: {e}")
            print("Trying to drop tables instead...")
            Base.metadata.drop_all(bind=engine)

    print("Recreating all tables...")
    Base.metadata.create_all(bind=engine)
    print("Reset complete.")

if __name__ == "__main__":
    reset()
