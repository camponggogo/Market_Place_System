"""
Migration: เพิ่มคอลัมน์ image_local, image_base64 ในตาราง menus
รันครั้งเดียวหลังจากอัปเดตโค้ด
"""
import sys
from pathlib import Path

# Add code/ to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text
from app.database import engine
from app.config import DB_NAME


def migrate():
    with engine.connect() as conn:
        # Check if image_local exists
        r = conn.execute(
            text(
                "SELECT COLUMN_NAME FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA = :db AND TABLE_NAME = 'menus' AND COLUMN_NAME = 'image_local'"
            ),
            {"db": DB_NAME},
        )
        if r.fetchone() is None:
            conn.execute(text("ALTER TABLE menus ADD COLUMN image_local VARCHAR(255) NULL"))
            conn.execute(text("ALTER TABLE menus ADD COLUMN image_base64 TEXT NULL"))
            conn.commit()
            print("Migration: Added image_local, image_base64 to menus")
        else:
            print("Migration: Columns already exist, skip")


if __name__ == "__main__":
    migrate()
