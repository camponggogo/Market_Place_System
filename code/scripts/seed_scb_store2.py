"""
ใส่ข้อมูล SCB PromptPay App (จาก scb.note) เข้า store_id=2
- เพิ่มคอลัมน์ scb_* ในตาราง stores ถ้ายังไม่มี (MySQL/MariaDB)
- อัปเดต store id=2 ด้วย API Key, API Secret, Callback URL

รันจากโฟลเดอร์ code: python scripts/seed_scb_store2.py
หรือจาก project root: python code/scripts/seed_scb_store2.py
"""
import sys
from pathlib import Path

# ให้ import app ได้ (รันจาก code/ หรือ project root)
code_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(code_dir))

from sqlalchemy import text
from app.database import engine, SessionLocal
from app.models import Store

# ค่าจาก scb.note สำหรับ store 2
STORE_ID = 2
SCB_APP_NAME = "QR-PromptPay-1"
SCB_API_KEY = "l79417b2c08a8c42b9b7d5c51210c01dbc"
SCB_API_SECRET = "9e96ab1086634cf4b7e4001ffec50908"
SCB_CALLBACK_URL = "http://150.95.85.185/webhook"


def add_columns_if_missing(conn):
    """เพิ่มคอลัมน์ scb_* ใน stores ถ้ายังไม่มี (MySQL duplicate column = ข้าม)"""
    columns = [
        ("scb_app_name", "VARCHAR(64) NULL"),
        ("scb_api_key", "VARCHAR(128) NULL"),
        ("scb_api_secret", "VARCHAR(255) NULL"),
        ("scb_callback_url", "VARCHAR(512) NULL"),
    ]
    for col_name, col_def in columns:
        try:
            conn.execute(text(f"ALTER TABLE stores ADD COLUMN {col_name} {col_def}"))
            conn.commit()
            print(f"  + column stores.{col_name}")
        except Exception as e:
            msg = str(e).lower()
            if "duplicate column" in msg or "1060" in msg or "already exists" in msg:
                print(f"  (column stores.{col_name} มีอยู่แล้ว)")
            else:
                raise


def main():
    print("Seed SCB config for store_id =", STORE_ID)

    # เพิ่มคอลัมน์ถ้ายังไม่มี
    with engine.connect() as conn:
        add_columns_if_missing(conn)

    db = SessionLocal()
    try:
        store = db.query(Store).filter(Store.id == STORE_ID).first()
        if not store:
            print(f"ไม่พบ store id={STORE_ID} ในฐานข้อมูล สร้างร้านก่อนหรือเปลี่ยน STORE_ID")
            return 1
        store.scb_app_name = SCB_APP_NAME
        store.scb_api_key = SCB_API_KEY
        store.scb_api_secret = SCB_API_SECRET
        store.scb_callback_url = SCB_CALLBACK_URL
        db.commit()
        print(f"อัปเดต store id={STORE_ID} (name={store.name}) ด้วย SCB App:", SCB_APP_NAME)
        print("  scb_callback_url =", SCB_CALLBACK_URL)
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
