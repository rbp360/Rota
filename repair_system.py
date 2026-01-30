
import os
import sys
import time

# Ensure backend folder is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from backend.database import engine, Base, SessionLocal
    from backend.normalize import normalize_data
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

def main():
    db_file = "rota.db"
    print(f"Checking for {db_file}...")
    
    # 1. Close connections/Kill (simulated by attempt to delete)
    if os.path.exists(db_file):
        print(f"Found {db_file}, attempting to delete to reset schema.")
        for i in range(3):
            try:
                os.remove(db_file)
                print("Deleted successfully.")
                break
            except Exception as e:
                print(f"Attempt {i+1} failed to delete: {e}")
                time.sleep(1)
        else:
            print("COULD NOT DELETE DB. It might be locked by the backend server.")
            print("Please stop your backend server (Ctrl+C in the terminal) and run this script again.")
            return

    # 2. Recreate schema
    print("Recreating database schema...")
    try:
        Base.metadata.create_all(bind=engine)
        print("Schema created successfully.")
    except Exception as e:
        print(f"Error creating schema: {e}")
        return

    # 3. Fill data
    print("Normalizing data from Excel...")
    try:
        normalize_data()
        print("Data normalization complete.")
    except Exception as e:
        print(f"Error during normalization: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
