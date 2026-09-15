"""
Database engine/session setup.

Reads DATABASE_URL from the environment. In production this should be a
PostgreSQL URL, e.g.:

    postgresql+psycopg2://wishtrip:wishtrip@localhost:5432/wishtrip_goa

For quick local development or running the test suite without a Postgres
instance, DATABASE_URL can be left unset and a local SQLite file
(`wishtrip_dev.db`) will be used instead. This fallback is explicitly a
developer convenience -- it is not part of the assignment's PostgreSQL
requirement and should not be used for the actual submission run.
"""
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./wishtrip_dev.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_session():
    """FastAPI-style dependency that yields a DB session and closes it after use."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()