"""
Migration: เปลี่ยน image_base64 จาก TEXT (64KB) เป็น MEDIUMTEXT (16MB)
เพื่อรองรับรูป base64 ที่มีขนาดใหญ่กว่า 64KB
รันครั้งเดียวหลังจากอัปเดตโค้ด
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
                "SELECT COLUMN_TYPE FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA = :db AND TABLE_NAME = 'menus' AND COLUMN_NAME = 'image_base64'"
            ),
            {"db": DB_NAME},
        )
        row = r.fetchone()
        if row is None:
            print("Migration: image_base64 column not found, skip")
            return
        col_type = (row[0] or "").upper()
        if "MEDIUMTEXT" in col_type:
            print("Migration: image_base64 already MEDIUMTEXT, skip")
            return
        conn.execute(text("ALTER TABLE menus MODIFY COLUMN image_base64 MEDIUMTEXT NULL"))
        conn.commit()
        print("Migration: Changed image_base64 from TEXT to MEDIUMTEXT")


if __name__ == "__main__":
    migrate()
