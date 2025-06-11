from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import contextlib

from src.config import DATABASE_URL

from .models import Base

import os

engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True to see SQL queries in console
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {} # Needed for SQLite with multiple threads
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@contextlib.contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
def init_db():
    """
    Creates all tables defined in models.py in the database.
    Call this function once when your application starts for the first time
    or when you want to recreate the database schema (e.g., in tests).
    """
    Base.metadata.create_all(bind=engine)
    print(f"Database initialized at: {DATABASE_URL}")
    
if __name__ == "__main__":
    init_db()
    