# File: app/database/session.py
# Part of EduGenie SmartBridge Project

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# SQLite connection adjustments for concurrent web operations
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

# Create Engine
engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args
)

# Enforce foreign key constraints inside SQLite database
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if settings.DATABASE_URL.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

# Session Maker
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Declarative base model
Base = declarative_base()

# FastAPI Dependency for Session injection
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
