from backend.database import engine, Base
import os

def init_db():
    print("Initializing database...")
    Base.metadata.create_all(bind=engine)
    print("Database initialized.")

if __name__ == "__main__":
    # Ensure engine is accessible
    from sqlalchemy import create_engine
    engine = create_engine("sqlite:///./rota.db", connect_args={"check_same_thread": False})
    
    # We need to import Staff, Schedule, etc. to register them with Base
    from backend.database import Staff, Schedule, Absence, Cover, Setting
    
    Base.metadata.create_all(bind=engine)
    print("Database tables created.")
