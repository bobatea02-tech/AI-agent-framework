import os
from contextlib import contextmanager
from typing import Generator
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Load environment variables
load_dotenv()

def get_database_url() -> str:
    """
    Get database URL from environment variable.
    Returns sqlite:///:memory: as fallback for testing/development if not set.
    """
    url = os.getenv("DATABASE_URL")
    if not url:
        # Fallback to in-memory sqlite for dev/test if not provided
        # In production this should likely raise an error
        return "sqlite:///./dev.db" 
    return url

# Create engine
# connect_args={"check_same_thread": False} is needed for SQLite
engine = create_engine(
    get_database_url(),
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    # Add check_same_thread for SQLite specifically if the URL indicates it, 
    # but strictly following user request for global params. 
    # However, to avoid crashes if user defaults to sqlite:
    connect_args={"check_same_thread": False} if "sqlite" in get_database_url() else {}
)

# Create SessionLocal
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI.
    Yields a database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager for general usage (non-FastAPI).
    Handles commit/rollback automatically.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
