"""
เพิ่มข้อมูลทดสอบสำหรับรายงานยอดโอนให้ร้านค้า (ทุกร้าน)
- อัปเดตข้อมูลธนาคารร้าน (เลขบัญชี, ชื่อธนาคาร, สาขา) ถ้ายังว่าง
- สร้าง PromptPayBackTransaction ปลอมในวันที่กำหนด เพื่อให้ออกรายงานได้
- สร้าง StoreSettlement รายวัน (ถ้าเป็นรายวัน) เพื่อทดสอบปุ่มสถานะการโอน

รันจากโฟลเดอร์โปรเจกต์:
  set PYTHONPATH=code
  python Run/seed_transfer_report_test_data.py

หรือ:
  python Run/seed_transfer_report_test_data.py --date 2026-03-08

อาร์กิวเมนต์:
  --date YYYY-MM-DD   วันที่ที่ต้องการใส่ข้อมูล (ค่าเริ่มต้น: วันนี้)
  --dry-run           แสดงว่าจะทำอะไร โดยไม่เขียน DB
"""
import sys
import argparse
from pathlib import Path
from datetime import datetime, date, time

# โฟลเดอร์ code/ (เพื่อ import app.*)
root = Path(__file__).resolve().parent.parent
code_dir = root / "code"
if not code_dir.exists():
    code_dir = root  # ถ้ารันจากใน code/
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from sqlalchemy import text
from app.database import SessionLocal, engine
from app.models import Store, PromptPayBackTransaction
from app.services.settlement_service import create_daily_settlements


def ensure_bank_columns():
    """เพิ่มคอลัมน์ bank_name, bank_branch ใน stores ถ้ายังไม่มี"""
    for col, defn in [("bank_name", "VARCHAR(128) NULL"), ("bank_branch", "VARCHAR(128) NULL")]:
        try:
            with engine.connect() as conn:
                conn.execute(text(f"ALTER TABLE stores ADD COLUMN {col} {defn}"))
                conn.commit()
                print(f"  + เพิ่มคอลัมน์ stores.{col}")
        except Exception as e:
            if "Duplicate column" in str(e) or "1060" in str(e):
                pass
            else:
                raise


# ยอดขายตัวอย่างแยกร้าน (บาท) — ใช้เรียงตาม store.id ถ้าร้านมากกว่าจำนวนตัวเลขจะวนใช้
SAMPLE_AMOUNTS = [550.00, 1200.00, 800.00, 2350.00, 6350.00, 410.00, 990.00, 1750.00, 3200.00, 500.00]


def ensure_store_bank_info(db, store: Store, dry_run: bool) -> bool:
    """ใส่หรืออัปเดตเลขบัญชี/ชื่อธนาคาร/สาขา ถ้ายังว่าง คืน True ถ้ามีการแก้"""
    updated = False
    if not (store.bank_account or "").strip():
        val = ("3251243213" + str(store.id).zfill(3))[:13]  # 13 หลัก ไม่ซ้ำกัน
        if not dry_run:
            store.bank_account = val
        print(f"  Store #{store.id} {store.name}: bank_account = {val}")
        updated = True
    if not (getattr(store, "bank_name", None) or "").strip():
        val = "ธนาคารทดสอบ (Test)"
        if not dry_run:
            store.bank_name = val
        if updated or not (getattr(store, "bank_branch", None) or "").strip():
            print(f"  Store #{store.id} {store.name}: bank_name = {val}")
        updated = True
    if not (getattr(store, "bank_branch", None) or "").strip():
        val = f"สาขาทดสอบ #{store.id}"
        if not dry_run:
            store.bank_branch = val
        print(f"  Store #{store.id} {store.name}: bank_branch = {val}")
        updated = True
    return updated


def seed_back_transactions(db, test_date: date, dry_run: bool) -> int:
    """สร้าง PromptPayBackTransaction ปลอมสำหรับทุกร้านใน test_date คืนจำนวนรายการที่สร้าง"""
    stores = db.query(Store).order_by(Store.id).all()
    if not stores:
        print("ไม่พบร้านค้าในระบบ ให้รัน seed_stores_menus_users.py ก่อน")
        return 0

    count = 0
    start_dt = datetime.combine(test_date, time(8, 0, 0))
    for i, store in enumerate(stores):
        amount = SAMPLE_AMOUNTS[i % len(SAMPLE_AMOUNTS)]
        ref1 = (store.token or "").strip() or str(store.id).zfill(20)
        if dry_run:
            print(f"  [dry-run] จะเพิ่ม BackTransaction store_id={store.id} ref1={ref1} amount={amount} paid_at={start_dt}")
            count += 1
            continue
        t = PromptPayBackTransaction(
            ref1=ref1,
            ref2="test-report",
            ref3=f"seed_transfer_report store_id={store.id}",
            amount=amount,
            paid_at=start_dt,
            store_id=store.id,
            status="received",
            payment_gateway="stripe",
        )
        db.add(t)
        count += 1
        # เลื่อนเวลาเล็กน้อยเพื่อไม่ซ้ำ
        start_dt = datetime.combine(test_date, time(8, (i + 1) % 60, 0))

    if not dry_run and count > 0:
        db.commit()
    return count


def main():
    parser = argparse.ArgumentParser(description="เพิ่มข้อมูลทดสอบรายงานยอดโอนให้ร้านค้า")
    parser.add_argument("--date", type=str, default=None, help="วันที่ (YYYY-MM-DD) ค่าเริ่มต้นคือวันนี้")
    parser.add_argument("--dry-run", action="store_true", help="แสดงอย่างเดียว ไม่เขียน DB")
    args = parser.parse_args()

    if args.date:
        try:
            test_date = datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            print("รูปแบบวันที่ต้องเป็น YYYY-MM-DD")
            sys.exit(1)
    else:
        test_date = date.today()

    print("=== เพิ่มข้อมูลทดสอบ รายงานยอดโอนให้ร้านค้า ===")
    print(f"วันที่ใช้: {test_date}")
    if args.dry_run:
        print("โหมด dry-run (ไม่เขียน DB)")
    print()

    # เตรียมคอลัมน์ bank_name, bank_branch ถ้ายังไม่มี
    print("ตรวจสอบคอลัมน์ stores.bank_name / bank_branch ...")
    ensure_bank_columns()

    db = SessionLocal()
    try:
        stores = db.query(Store).order_by(Store.id).all()
        print(f"พบร้านค้า {len(stores)} ร้าน")
        if not stores:
            print("ไม่มีร้านในระบบ ให้รัน seed_stores_menus_users.py ก่อน")
            return

        # 1) อัปเดตข้อมูลธนาคารร้าน (ถ้าว่าง)
        print("\n1) ข้อมูลธนาคารร้าน (เลขบัญชี / ชื่อธนาคาร / สาขา)")
        bank_updated = False
        for store in stores:
            if ensure_store_bank_info(db, store, args.dry_run):
                bank_updated = True
        if bank_updated and not args.dry_run:
            db.commit()
            print("  บันทึกแล้ว")
        elif not bank_updated:
            print("  ทุกร้านมีข้อมูลธนาคารแล้ว")

        # 2) สร้าง Back Transaction ปลอม
        print("\n2) สร้าง PromptPayBackTransaction (ยอดขายปลอม) ในวันที่เลือก")
        n = seed_back_transactions(db, test_date, args.dry_run)
        print(f"  สร้างรายการแล้ว {n} รายการ")

        # 3) สร้าง StoreSettlement รายวัน เพื่อให้หน้ารายงานแสดงสถานะการโอนได้
        print("\n3) สร้าง StoreSettlement รายวัน (สำหรับปุ่มสถานะการโอน)")
        if args.dry_run:
            print("  [dry-run] จะเรียก create_daily_settlements(db, test_date)")
        else:
            created = create_daily_settlements(db, test_date)
            print(f"  สร้าง/มีอยู่แล้ว {len(created)} รายการ")

        print("\nเสร็จแล้ว — เปิดหน้ารายงาน Admin > รายงานยอดโอนให้ร้านค้า")
        print("  เลือกวันที่ " + str(test_date) + " แล้วกด โหลดรายงาน")
    finally:
        db.close()


if __name__ == "__main__":
    main()
