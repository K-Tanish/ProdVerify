from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker

from backend.app.config import DATABASE_URL

# Enable foreign keys for SQLite connections
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if type(dbapi_connection).__module__.startswith("sqlite3"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

# Create SQLAlchemy engine
# connect_args={"check_same_thread": False} is required for SQLite multithreading in FastAPI
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Yield a database session and ensure clean close."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(target_engine=None):
    """Create all database tables."""
    eng = target_engine or engine
    # Import models to ensure they are registered with Base.metadata
    from backend.app import models  # noqa: F401

    Base.metadata.create_all(bind=eng)


def drop_db(target_engine=None):
    """Drop all database tables."""
    eng = target_engine or engine
    from backend.app import models  # noqa: F401

    Base.metadata.drop_all(bind=eng)
