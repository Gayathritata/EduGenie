# File: app/database/session.py
# Part of EduGenie SmartBridge Project

import logging
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

logger = logging.getLogger("edugenie")

# SQLite connection adjustments for concurrent web operations
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

# Create Engine
# pool_pre_ping=True  — validates each pooled connection before use,
#                       ensuring PRAGMA foreign_keys=ON fires on every connection.
# pool_recycle=1800   — recycles connections older than 30 min to prevent stale handles.
engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
    pool_recycle=1800,
)

# Enforce foreign key constraints and enable WAL mode on every new SQLite connection.
# WAL (Write-Ahead Logging) allows concurrent reads while a write is in progress,
# which significantly improves performance under FastAPI's async request workload.
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if settings.DATABASE_URL.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()
        logger.debug("SQLite PRAGMAs applied: foreign_keys=ON, journal_mode=WAL")

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
    """
    Yields a SQLAlchemy session for the duration of a single request.
    Always closes the session in the finally block to prevent connection leaks.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
