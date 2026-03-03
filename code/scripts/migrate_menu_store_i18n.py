"""
Migration: เพิ่มคอลัมน์ name_i18n, description_i18n ใน menus และ name_i18n ใน stores
สำหรับรองรับหลายภาษา
รันครั้งเดียว: python scripts/migrate_menu_store_i18n.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text
from app.database import engine
from app.config import DB_NAME


def migrate():
    with engine.connect() as conn:
        for table, cols in [
            ("menus", [("name_i18n", "TEXT NULL"), ("description_i18n", "TEXT NULL")]),
            ("stores", [("name_i18n", "TEXT NULL")]),
        ]:
            for col_name, col_def in cols:
                r = conn.execute(
                    text(
                        "SELECT COLUMN_NAME FROM information_schema.COLUMNS "
                        "WHERE TABLE_SCHEMA = :db AND TABLE_NAME = :tbl AND COLUMN_NAME = :col"
                    ),
                    {"db": DB_NAME, "tbl": table, "col": col_name},
                )
                if r.fetchone() is None:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_def}"))
                    conn.commit()
                    print(f"Migration: Added {col_name} to {table}")
                else:
                    print(f"Migration: {col_name} already exists in {table}, skip")


if __name__ == "__main__":
    migrate()
    print("Migration: menu/store i18n done")
