"""
รีเซ็ตร้านค้าสำหรับทดสอบ:
- ตั้ง group_id=0, site_id=0
- สร้าง store.token ใหม่ (20 หลัก)
- ตั้ง biller_id (ใช้ค่าทดสอบ 011556400219809 หรือจาก tax_id+99)
"""
import sys
from pathlib import Path

root_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(root_dir))

from app.config import DB_NAME, DB_HOST, DB_PORT, DB_USER, DB_PASSWORD
from app.utils.store_token import generate_store_token
import pymysql

# Biller ID สำหรับทดสอบ (15 หลัก)
TEST_BILLER_ID = "011556400219809"


def reset_stores_for_test(use_test_biller_id: bool = True):
    """
    - ตั้ง group_id=0, site_id=0 ทุกร้าน
    - สร้าง token ใหม่จาก (0, 0, store_id, 0)
    - ตั้ง biller_id = TEST_BILLER_ID ถ้า use_test_biller_id อย่างอื่นจาก tax_id+99
    """
    try:
        print(f"Connecting to MariaDB at {DB_HOST}:{DB_PORT}...")
        connection = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset="utf8mb4",
        )

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, COALESCE(tax_id,'') AS tax_id FROM stores"
            )
            rows = cursor.fetchall()

            for store_id, tax_id in rows:
                # group_id=0, site_id=0
                gid, sid = 0, 0
                token = generate_store_token(
                    group_id=gid,
                    site_id=sid,
                    store_id=store_id,
                    menu_id=0,
                )
                if use_test_biller_id:
                    biller_id = TEST_BILLER_ID
                else:
                    tax_clean = "".join(c for c in str(tax_id) if c.isdigit())
                    biller_id = (tax_clean + "99")[:15].zfill(15) if tax_clean else TEST_BILLER_ID

                cursor.execute(
                    """UPDATE stores
                       SET group_id = %s, site_id = %s, token = %s, biller_id = %s
                       WHERE id = %s""",
                    (gid, sid, token, biller_id, store_id),
                )
                print(f"  Store id={store_id} -> token={token} biller_id={biller_id}")

            connection.commit()
            print(f"[OK] Reset {len(rows)} store(s) for test. ref1=store.token, biller_id=store.biller_id")
        connection.close()
        return True
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Reset stores for test: group_id=0, site_id=0, new token, biller_id")
    parser.add_argument("--biller-from-tax", action="store_true", help="Use tax_id+99 for biller_id instead of test value")
    args = parser.parse_args()
    print("=" * 60)
    print("Reset stores for test (group_id=0, site_id=0, new token, biller_id)")
    print("=" * 60)
    reset_stores_for_test(use_test_biller_id=not args.biller_from_tax)
