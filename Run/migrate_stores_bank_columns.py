"""
Migration: เพิ่มคอลัมน์ SCB และ K Bank ในตาราง stores
(scb_app_name, scb_api_key, scb_api_secret, scb_callback_url, kbank_customer_id, kbank_consumer_secret)
รันจาก project root: PYTHONPATH=code python Run/migrate_stores_bank_columns.py
"""
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent / "code"
sys.path.insert(0, str(root_dir))

from app.config import DB_NAME, DB_HOST, DB_PORT, DB_USER, DB_PASSWORD
import pymysql

COLUMNS = [
    ("scb_app_name", "VARCHAR(64) NULL"),
    ("scb_api_key", "VARCHAR(128) NULL"),
    ("scb_api_secret", "VARCHAR(255) NULL"),
    ("scb_callback_url", "VARCHAR(512) NULL"),
    ("kbank_customer_id", "VARCHAR(128) NULL"),
    ("kbank_consumer_secret", "VARCHAR(255) NULL"),
]


def migrate():
    try:
        print(f"Connecting to {DB_HOST}:{DB_PORT}/{DB_NAME}...")
        conn = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset="utf8mb4",
        )
        with conn.cursor() as cur:
            for col_name, col_def in COLUMNS:
                cur.execute("SHOW COLUMNS FROM stores LIKE %s", (col_name,))
                if cur.fetchone():
                    print(f"  Column stores.{col_name} already exists.")
                else:
                    print(f"  Adding stores.{col_name}...")
                    cur.execute(f"ALTER TABLE stores ADD COLUMN {col_name} {col_def}")
        conn.commit()
        conn.close()
        print("Done.")
        return 0
    except Exception as e:
        print("Error:", e)
        return 1


if __name__ == "__main__":
    sys.exit(migrate())
