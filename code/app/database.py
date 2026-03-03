"""
Database connection and session management
"""
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import DATABASE_URL

# MariaDB/MySQL connection settings
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,   # Verify connections before using (fixes stale connection)
    pool_recycle=3600,    # Recycle connections after 1 hour
    pool_size=5,          # Connection pool size
    max_overflow=10,      # Extra connections when pool exhausted
    connect_args={"connect_timeout": 10},  # Connection timeout (seconds)
    echo=False            # Set to True for SQL query debugging
)


def check_db_connection():
    """ตรวจสอบการเชื่อมต่อ DB คืน (success, message)"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, "OK"
    except Exception as e:
        return False, str(e)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

