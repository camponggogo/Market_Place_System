# Create banking_profiles table (run from project root: PYTHONPATH=code python Run/migrate_banking_profiles.py)
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "code"))

from app.database import engine
from app.models import Base
import app.models  # noqa: F401

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print("banking_profiles table created if not exists.")
