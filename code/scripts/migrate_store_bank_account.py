"""
Migration: เพิ่มคอลัมน์ bank_account ใน stores (เลขที่บัญชีร้าน สำหรับรายงานสรุปยอด)
รันครั้งเดียว: จากโฟลเดอร์ code: python scripts/migrate_store_bank_account.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text
from app.database import engine

def run():
    with engine.connect() as conn:
        # MySQL/MariaDB: add column if not exists
        try:
            conn.execute(text("""
                ALTER TABLE stores ADD COLUMN bank_account VARCHAR(50) NULL
                COMMENT 'เลขที่บัญชีร้าน สำหรับโอนเงิน/รายงาน'
            """))
            conn.commit()
            print("Migration: stores.bank_account added.")
        except Exception as e:
            if "Duplicate column" in str(e) or "1060" in str(e):
                print("Migration: stores.bank_account already exists, skip.")
            else:
                raise

if __name__ == "__main__":
    run()
