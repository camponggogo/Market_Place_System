"""
ใส่ข้อมูล K Bank (K API) จาก K_API.note เข้า store_id=2
- เพิ่มคอลัมน์ kbank_customer_id, kbank_consumer_secret ใน stores ถ้ายังไม่มี
- อัปเดต store id=2 ด้วย Customer ID และ Consumer Secret

รันจาก project root: python code/scripts/seed_kbank_store2.py
หรือจาก code: python scripts/seed_kbank_store2.py
"""
import sys
from pathlib import Path

code_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(code_dir))

from sqlalchemy import text
from app.database import engine, SessionLocal
from app.models import Store

# ค่าจาก K_API.note (K Bank apiportal.kasikornbank.com)
STORE_ID = 2
KBANK_CUSTOMER_ID = "sORg8e7ZIfvAcYe8gEZkkpUuf52BjUTc"
KBANK_CONSUMER_SECRET = "mohvoISR9I0pgtcf"


def add_columns_if_missing(conn):
    """เพิ่มคอลัมน์ kbank_* ใน stores ถ้ายังไม่มี"""
    columns = [
        ("kbank_customer_id", "VARCHAR(128) NULL"),
        ("kbank_consumer_secret", "VARCHAR(255) NULL"),
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
    print("Seed K Bank (K API) config for store_id =", STORE_ID)

    with engine.connect() as conn:
        add_columns_if_missing(conn)

    db = SessionLocal()
    try:
        store = db.query(Store).filter(Store.id == STORE_ID).first()
        if not store:
            print(f"ไม่พบ store id={STORE_ID} ในฐานข้อมูล สร้างร้านก่อนหรือเปลี่ยน STORE_ID")
            return 1
        store.kbank_customer_id = KBANK_CUSTOMER_ID
        store.kbank_consumer_secret = KBANK_CONSUMER_SECRET
        db.commit()
        print(f"อัปเดต store id={STORE_ID} (name={store.name}) ด้วย K Bank K API")
        print("  kbank_customer_id =", KBANK_CUSTOMER_ID[:16] + "...")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
