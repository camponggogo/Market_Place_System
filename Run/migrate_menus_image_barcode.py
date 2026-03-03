"""
Migration: เพิ่ม image_url และ barcode ใน menus
Run: python Run/migrate_menus_image_barcode.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "code"))

from sqlalchemy import text
from app.database import engine

# Detect DB type from engine URL
db_url = str(engine.url)
is_sqlite = "sqlite" in db_url

def migrate():
    with engine.connect() as conn:
        existing = set()
        if is_sqlite:
            r = conn.execute(text("PRAGMA table_info(menus)"))
            existing = {row[1] for row in r}
        else:
            r = conn.execute(text("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'menus' AND column_name IN ('image_url', 'barcode')
            """))
            existing = {row[0] for row in r}
        if "image_url" not in existing:
            conn.execute(text("ALTER TABLE menus ADD COLUMN image_url VARCHAR(512)"))
            conn.commit()
            print("Added menus.image_url")
        if "barcode" not in existing:
            conn.execute(text("ALTER TABLE menus ADD COLUMN barcode VARCHAR(64)"))
            conn.commit()
            try:
                conn.execute(text("CREATE INDEX ix_menus_barcode ON menus(barcode)"))
                conn.commit()
            except Exception:
                pass
            print("Added menus.barcode")
        else:
            print("Columns already exist")

if __name__ == "__main__":
    migrate()
