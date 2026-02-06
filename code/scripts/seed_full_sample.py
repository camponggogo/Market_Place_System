"""
Seed ข้อมูลตัวอย่าง + ข้อมูลจาก scb.note ลง database: market_place_system @ localhost
สำหรับทดสอบ full-loop (Store-POS, QR, Webhook, Signage)

- สร้าง DB market_place_system ถ้ายังไม่มี
- สร้างตารางทั้งหมด (create_all)
- เพิ่มคอลัมน์ scb_* ใน stores ถ้ายังไม่มี
- ใส่ข้อมูล: Profile, Store 1 & 2 (store 2 มี SCB จาก scb.note), Menus, StoreQuickAmounts

รันจาก project root: python code/scripts/seed_full_sample.py
หรือจาก code: python scripts/seed_full_sample.py
"""
import sys
from pathlib import Path

code_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(code_dir))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# ใช้ config แต่บังคับ DB = market_place_system, Host = localhost
from app.config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD

DB_NAME = "market_place_system"
HOST = "localhost"

# Engine ชั่วคราว (ไม่ระบุ DB) สำหรับสร้าง database
URL_NO_DB = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{HOST}:{DB_PORT}/?charset=utf8mb4"
# Engine หลักชี้ไปที่ market_place_system
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

# ค่าจาก scb.note สำหรับ store 2
SCB_APP_NAME = "QR-PromptPay-1"
SCB_API_KEY = "l79417b2c08a8c42b9b7d5c51210c01dbc"
SCB_API_SECRET = "9e96ab1086634cf4b7e4001ffec50908"
SCB_CALLBACK_URL = "http://150.95.85.185/webhook"

# ค่าจาก K_API.note สำหรับ store 2 (K Bank QR Payment)
KBANK_CUSTOMER_ID = "sORg8e7ZIfvAcYe8gEZkkpUuf52BjUTc"
KBANK_CONSUMER_SECRET = "mohvoISR9I0pgtcf"


def ensure_database():
    """สร้าง database market_place_system ถ้ายังไม่มี"""
    engine = create_engine(URL_NO_DB, isolation_level="AUTOCOMMIT")
    with engine.connect() as conn:
        conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
    engine.dispose()
    print(f"  DB: {DB_NAME} @ {HOST}")


def add_scb_columns(conn):
    """เพิ่มคอลัมน์ scb_* ใน stores ถ้ายังไม่มี"""
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
            print(f"  + stores.{col_name}")
        except Exception as e:
            msg = str(e).lower()
            if "duplicate column" in msg or "1060" in msg or "already exists" in msg:
                pass
            else:
                raise


def add_kbank_columns(conn):
    """เพิ่มคอลัมน์ K Bank (K API) ใน stores ถ้ายังไม่มี"""
    columns = [
        ("kbank_customer_id", "VARCHAR(128) NULL"),
        ("kbank_consumer_secret", "VARCHAR(255) NULL"),
    ]
    for col_name, col_def in columns:
        try:
            conn.execute(text(f"ALTER TABLE stores ADD COLUMN {col_name} {col_def}"))
            conn.commit()
            print(f"  + stores.{col_name}")
        except Exception as e:
            msg = str(e).lower()
            if "duplicate column" in msg or "1060" in msg or "already exists" in msg:
                pass
            else:
                raise


def main():
    print("=== Seed Full Sample -> market_place_system @ localhost ===\n")

    ensure_database()

    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    # โหลด models เพื่อให้ Base.metadata มีทุกตาราง
    from app.database import Base
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    print("  Tables: create_all OK")

    with engine.connect() as conn:
        add_scb_columns(conn)
        add_kbank_columns(conn)

    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = Session()

    from app.models import Profile, Event, Store, Menu, StoreQuickAmount
    from app.utils.store_token import generate_store_token

    try:
        # --- Profile ---
        profile = db.query(Profile).filter(Profile.name == "Food Court ทดสอบ").first()
        if not profile:
            profile = Profile(
                name="Food Court ทดสอบ",
                description="Profile สำหรับทดสอบ full-loop",
                profile_type="store_rental",
                is_active=True,
            )
            db.add(profile)
            db.commit()
            db.refresh(profile)
            print("  + Profile: Food Court ทดสอบ")
        else:
            print("  (Profile มีอยู่แล้ว)")

        # --- Store 1 ---
        store1 = db.query(Store).filter(Store.id == 1).first()
        if not store1:
            store1 = Store(
                name="ร้านทดสอบ 1",
                tax_id="",
                crypto_enabled=False,
                contract_accepted=True,
                group_id=1,
                site_id=1,
                profile_id=profile.id,
            )
            db.add(store1)
            db.commit()
            db.refresh(store1)
            store1.token = generate_store_token(group_id=1, site_id=1, store_id=store1.id, menu_id=0)
            db.commit()
            print("  + Store 1:", store1.name, "token:", store1.token)
        else:
            if not store1.token:
                store1.token = generate_store_token(group_id=1, site_id=1, store_id=1, menu_id=0)
                db.commit()
            print("  Store 1:", store1.name, "token:", store1.token)

        # --- Store 2 (พร้อม SCB จาก scb.note) ---
        store2 = db.query(Store).filter(Store.id == 2).first()
        if not store2:
            store2 = Store(
                name="ร้านทดสอบ 2 (PromptPay)",
                tax_id="",
                crypto_enabled=False,
                contract_accepted=True,
                group_id=1,
                site_id=1,
                profile_id=profile.id,
                scb_app_name=SCB_APP_NAME,
                scb_api_key=SCB_API_KEY,
                scb_api_secret=SCB_API_SECRET,
                scb_callback_url=SCB_CALLBACK_URL,
                kbank_customer_id=KBANK_CUSTOMER_ID,
                kbank_consumer_secret=KBANK_CONSUMER_SECRET,
            )
            db.add(store2)
            db.commit()
            db.refresh(store2)
            store2.token = generate_store_token(group_id=1, site_id=1, store_id=store2.id, menu_id=0)
            db.commit()
            print("  + Store 2:", store2.name, "token:", store2.token, "| SCB:", SCB_APP_NAME, "| K Bank: OK")
        else:
            store2.scb_app_name = SCB_APP_NAME
            store2.scb_api_key = SCB_API_KEY
            store2.scb_api_secret = SCB_API_SECRET
            store2.scb_callback_url = SCB_CALLBACK_URL
            store2.kbank_customer_id = KBANK_CUSTOMER_ID
            store2.kbank_consumer_secret = KBANK_CONSUMER_SECRET
            if not store2.token:
                store2.token = generate_store_token(group_id=1, site_id=1, store_id=2, menu_id=0)
            db.commit()
            print("  Store 2:", store2.name, "| SCB + K Bank อัปเดตแล้ว")

        # --- Menus (Store 1 & 2) ---
        for store, items in [
            (store1, [("ข้าวผัด", 45.0), ("ก๋วยเตี๋ยว", 50.0), ("น้ำเปล่า", 10.0)]),
            (store2, [("ข้าวมันไก่", 50.0), ("กาแฟ", 35.0), ("น้ำอัดลม", 15.0)]),
        ]:
            for name, price in items:
                exists = db.query(Menu).filter(Menu.store_id == store.id, Menu.name == name).first()
                if not exists:
                    db.add(Menu(store_id=store.id, name=name, unit_price=price, is_active=True))
            db.commit()
        print("  + Menus: ร้าน 1 & 2")

        # --- StoreQuickAmounts (50, 100, 200 บาท) ---
        for store in [store1, store2]:
            for amt, label in [(50, "50 บาท"), (100, "100 บาท"), (200, "200 บาท")]:
                exists = (
                    db.query(StoreQuickAmount)
                    .filter(StoreQuickAmount.store_id == store.id, StoreQuickAmount.amount == amt)
                    .first()
                )
                if not exists:
                    db.add(
                        StoreQuickAmount(
                            store_id=store.id,
                            amount=float(amt),
                            label=label,
                            display_order=amt,
                            is_active=True,
                        )
                    )
            db.commit()
        print("  + StoreQuickAmounts: 50, 100, 200 บาท (ร้าน 1 & 2)")

        print("\n--- สรุป ---")
        print("  Store 1: id=1, token (ref1) =", store1.token)
        print("  Store 2: id=2, token (ref1) =", store2.token, "| SCB Callback:", SCB_CALLBACK_URL)
        print("  ใช้ ref1 = token ของร้านตอนทดสอบ Webhook / Back Transaction")
        print("\nเสร็จแล้ว. ตั้ง config.ini หรือ env ให้ DB_NAME=market_place_system แล้วรัน backend เพื่อทดสอบ full-loop")

    finally:
        db.close()
        engine.dispose()

    return 0


if __name__ == "__main__":
    sys.exit(main())
