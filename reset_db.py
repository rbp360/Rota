from backend.database import engine, Base
import os

def reset():
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("Recreating all tables...")
    Base.metadata.create_all(bind=engine)
    print("Reset complete.")

if __name__ == "__main__":
    reset()
