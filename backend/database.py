from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, Date, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

SQLALCHEMY_DATABASE_URL = "sqlite:///./rota.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Staff(Base):
    __tablename__ = "staff"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    role = Column(String)  # Teacher or TA
    profile = Column(Text, nullable=True)
    is_priority = Column(Boolean, default=False)
    is_specialist = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    schedules = relationship("Schedule", back_populates="staff")
    absences = relationship("Absence", back_populates="staff")

class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    staff_id = Column(Integer, ForeignKey("staff.id"))
    day_of_week = Column(String)  # Monday, Tuesday, etc.
    period = Column(Integer)
    activity = Column(String)
    location = Column(String, nullable=True)
    is_free = Column(Boolean, default=False)

    staff = relationship("Staff", back_populates="schedules")

class Absence(Base):
    __tablename__ = "absences"

    id = Column(Integer, primary_key=True, index=True)
    staff_id = Column(Integer, ForeignKey("staff.id"))
    date = Column(Date)
    start_period = Column(Integer)
    end_period = Column(Integer)
    reason = Column(String, nullable=True)

    staff = relationship("Staff", back_populates="absences")
    covers = relationship("Cover", back_populates="absence")

class Cover(Base):
    __tablename__ = "covers"

    id = Column(Integer, primary_key=True, index=True)
    absence_id = Column(Integer, ForeignKey("absences.id"))
    covering_staff_id = Column(Integer, ForeignKey("staff.id"))
    period = Column(Integer)
    reason_for_selection = Column(Text)
    status = Column(String, default="pending")  # pending, confirmed, rejected

    absence = relationship("Absence", back_populates="covers")
    covering_staff = relationship("Staff")

class Setting(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    value = Column(Text)
