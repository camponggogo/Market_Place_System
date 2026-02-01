"""
Migration: สร้างตาราง promptpay_back_transactions และ store_settlements
สำหรับรับ Back Transaction, รายงาน, รายการโอนสิ้นวัน, แจ้งร้าน
"""
import sys
from pathlib import Path

root_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(root_dir))

from app.database import engine, Base
from app.models import PromptPayBackTransaction, StoreSettlement

if __name__ == "__main__":
    print("Creating settlement tables (promptpay_back_transactions, store_settlements)...")
    Base.metadata.create_all(bind=engine, tables=[PromptPayBackTransaction.__table__, StoreSettlement.__table__])
    print("[OK] Done.")
