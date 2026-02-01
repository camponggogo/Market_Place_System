"""
Migration: เพิ่มคอลัมน์ ref1, ref2, ref3, bank_account ในตาราง transactions
และ bank_account ใน promptpay_back_transactions (ถ้ายังไม่มี)
ถ้าตาราง promptpay_back_transactions ยังไม่มี จะสร้างก่อน (เหมือน migrate_settlement_tables)
"""
import sys
from pathlib import Path

root_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(root_dir))

from app.config import DB_NAME, DB_HOST, DB_PORT, DB_USER, DB_PASSWORD
from app.database import engine, Base
from app.models import PromptPayBackTransaction, StoreSettlement
import pymysql


def migrate():
    try:
        conn = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset="utf8mb4",
        )
        cur = conn.cursor()
        # สร้างตาราง promptpay_back_transactions, store_settlements ก่อนถ้ายังไม่มี
        cur.execute("SHOW TABLES LIKE 'promptpay_back_transactions'")
        if not cur.fetchone():
            cur.close()
            conn.close()
            print("  Creating tables promptpay_back_transactions, store_settlements...")
            Base.metadata.create_all(
                bind=engine,
                tables=[PromptPayBackTransaction.__table__, StoreSettlement.__table__],
            )
            print("  [OK] Tables created.")
            conn = pymysql.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                charset="utf8mb4",
            )
            cur = conn.cursor()

        # transactions
        specs = [
            ("ref1", "VARCHAR(20) NULL"),
            ("ref2", "VARCHAR(50) NULL"),
            ("ref3", "VARCHAR(255) NULL"),
            ("bank_account", "VARCHAR(50) NULL"),
        ]
        for col, spec in specs:
            cur.execute("SHOW COLUMNS FROM transactions LIKE %s", (col,))
            if not cur.fetchone():
                cur.execute(f"ALTER TABLE transactions ADD COLUMN {col} {spec}")
                if col == "ref1":
                    cur.execute("ALTER TABLE transactions ADD INDEX idx_transactions_ref1 (ref1)")
                print(f"  transactions: added {col}")
        # promptpay_back_transactions - เพิ่ม bank_account ถ้ายังไม่มี
        cur.execute("SHOW TABLES LIKE 'promptpay_back_transactions'")
        if cur.fetchone():
            cur.execute("SHOW COLUMNS FROM promptpay_back_transactions LIKE 'bank_account'")
            if not cur.fetchone():
                cur.execute("ALTER TABLE promptpay_back_transactions ADD COLUMN bank_account VARCHAR(50) NULL")
                print("  promptpay_back_transactions: added bank_account")
        conn.commit()
        cur.close()
        conn.close()
        print("[OK] Migration done.")
        return True
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Migrate transactions: ref1, ref2, ref3, bank_account")
    migrate()
