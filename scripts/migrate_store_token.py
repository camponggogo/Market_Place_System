"""
Migration: เพิ่มคอลัมน์ group_id, site_id, token ใน stores และเติม token ให้ร้านค้าที่มีอยู่
Token 20 หลัก = group_id(3) + site_id(4) + store_id(6) + menu_id(7)
"""
import sys
from pathlib import Path

root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from app.config import DB_NAME, DB_HOST, DB_PORT, DB_USER, DB_PASSWORD
from app.utils.store_token import generate_store_token
import pymysql


def migrate_store_token():
    """เพิ่ม group_id, site_id, token และเติม token ให้ร้านค้าทั้งหมด"""
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
            cursor.execute("SHOW COLUMNS FROM stores LIKE 'group_id'")
            has_group_id = cursor.fetchone()
            cursor.execute("SHOW COLUMNS FROM stores LIKE 'site_id'")
            has_site_id = cursor.fetchone()
            cursor.execute("SHOW COLUMNS FROM stores LIKE 'token'")
            has_token = cursor.fetchone()
            cursor.execute("SHOW COLUMNS FROM stores LIKE 'biller_id'")
            has_biller_id = cursor.fetchone()

            if not has_group_id:
                print("Adding column group_id...")
                cursor.execute(
                    "ALTER TABLE stores ADD COLUMN group_id INT NOT NULL DEFAULT 0"
                )
            if not has_site_id:
                print("Adding column site_id...")
                cursor.execute(
                    "ALTER TABLE stores ADD COLUMN site_id INT NOT NULL DEFAULT 0"
                )
            if not has_token:
                print("Adding column token...")
                cursor.execute(
                    "ALTER TABLE stores ADD COLUMN token VARCHAR(20) NULL UNIQUE"
                )
            if not has_biller_id:
                print("Adding column biller_id...")
                cursor.execute(
                    "ALTER TABLE stores ADD COLUMN biller_id VARCHAR(15) NULL"
                )
            if not has_group_id or not has_site_id or not has_token or not has_biller_id:
                connection.commit()
                print("[OK] New columns added.")
            else:
                print("[OK] Columns group_id, site_id, token, biller_id already exist.")

            # เติม token ให้ร้านค้าที่ยังไม่มี token
            cursor.execute(
                "SELECT id, COALESCE(group_id, 0) AS gid, COALESCE(site_id, 0) AS sid FROM stores"
            )
            rows = cursor.fetchall()
            updated = 0
            for row in rows:
                store_id, group_id, site_id = row
                try:
                    gid = int(group_id) if group_id is not None else 0
                except (ValueError, TypeError):
                    gid = 0
                try:
                    sid = int(site_id) if site_id is not None else 0
                except (ValueError, TypeError):
                    sid = 0
                token = generate_store_token(
                    group_id=gid,
                    site_id=sid,
                    store_id=store_id,
                    menu_id=0,
                )
                cursor.execute(
                    "UPDATE stores SET token = %s WHERE id = %s AND (token IS NULL OR token = '')",
                    (token, store_id),
                )
                if cursor.rowcount:
                    updated += 1
                    print(f"  Store id={store_id} -> token={token}")

            connection.commit()
            print(f"[OK] Filled token for {updated} store(s). Total stores: {len(rows)}.")
        connection.close()
        return True
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Migrate stores: add token (20-digit store token)")
    print("=" * 60)
    migrate_store_token()
