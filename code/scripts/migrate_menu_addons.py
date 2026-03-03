"""
Migration: เพิ่มคอลัมน์ addon_options ในตาราง menus
สำหรับท็อปปิ้ง/พิเศษ/เพิ่มเติม (JSON: [{ "name": "ไข่ดาว", "price": 10 }])
รันครั้งเดียว: python scripts/migrate_menu_addons.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text
from app.database import engine
from app.config import DB_NAME


def migrate():
    with engine.connect() as conn:
        r = conn.execute(
            text(
                "SELECT COLUMN_NAME FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA = :db AND TABLE_NAME = 'menus' AND COLUMN_NAME = 'addon_options'"
            ),
            {"db": DB_NAME},
        )
        if r.fetchone() is None:
            conn.execute(text("ALTER TABLE menus ADD COLUMN addon_options TEXT NULL"))
            conn.commit()
            print("Migration: Added addon_options to menus")
        else:
            print("Migration: addon_options already exists, skip")


if __name__ == "__main__":
    migrate()
