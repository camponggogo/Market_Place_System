"""
Migration: สร้าง/เพิ่มตารางสำหรับระบบลูกค้าสมาชิกออนไลน์
- customers: เพิ่ม username, email, password_hash, total_points
- member_points_ledger, voucher_definitions, member_vouchers
- store_promotions, e_coupons, ad_feeds, member_activities
รัน: python scripts/migrate_member_online.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text
from app.database import engine


def run_sql(conn, sql: str):
    for stmt in (s.strip() for s in sql.strip().split(";") if s.strip() and not s.strip().startswith("--")):
        conn.execute(text(stmt))


def main():
    with engine.connect() as conn:
        # เพิ่มคอลัมน์ใน customers (MySQL ไม่มี ADD COLUMN IF NOT EXISTS)
        for col, defn in [
            ("username", "VARCHAR(64) NULL UNIQUE"),
            ("email", "VARCHAR(255) NULL UNIQUE"),
            ("password_hash", "VARCHAR(255) NULL"),
            ("total_points", "FLOAT NOT NULL DEFAULT 0"),
        ]:
            try:
                conn.execute(text(f"ALTER TABLE customers ADD COLUMN `{col}` {defn}"))
            except Exception:
                pass  # มีอยู่แล้ว
        conn.commit()

        # ตารางใหม่
        run_sql(conn, """
        CREATE TABLE IF NOT EXISTS member_points_ledger (
            id INT AUTO_INCREMENT PRIMARY KEY,
            customer_id INT NOT NULL,
            points_delta FLOAT NOT NULL,
            balance_after FLOAT NOT NULL,
            reason VARCHAR(100) NULL,
            ref_id INT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            KEY ix_mp_customer (customer_id),
            CONSTRAINT fk_mp_customer FOREIGN KEY (customer_id) REFERENCES customers(id)
        );
        """)
        run_sql(conn, """
        CREATE TABLE IF NOT EXISTS voucher_definitions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            voucher_type VARCHAR(50) NOT NULL DEFAULT 'discount',
            value FLOAT NOT NULL,
            store_id INT NULL,
            valid_from DATETIME NULL,
            valid_to DATETIME NULL,
            is_active TINYINT(1) NOT NULL DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            KEY ix_vd_store (store_id),
            CONSTRAINT fk_vd_store FOREIGN KEY (store_id) REFERENCES stores(id)
        );
        """)
        run_sql(conn, """
        CREATE TABLE IF NOT EXISTS member_vouchers (
            id INT AUTO_INCREMENT PRIMARY KEY,
            customer_id INT NOT NULL,
            voucher_definition_id INT NOT NULL,
            code VARCHAR(64) NULL,
            used_at DATETIME NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            KEY ix_mv_customer (customer_id),
            KEY ix_mv_vdef (voucher_definition_id),
            CONSTRAINT fk_mv_customer FOREIGN KEY (customer_id) REFERENCES customers(id),
            CONSTRAINT fk_mv_vdef FOREIGN KEY (voucher_definition_id) REFERENCES voucher_definitions(id)
        );
        """)
        run_sql(conn, """
        CREATE TABLE IF NOT EXISTS store_promotions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            store_id INT NOT NULL,
            title VARCHAR(255) NOT NULL,
            description TEXT NULL,
            valid_from DATETIME NULL,
            valid_to DATETIME NULL,
            is_active TINYINT(1) NOT NULL DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            KEY ix_sp_store (store_id),
            CONSTRAINT fk_sp_store FOREIGN KEY (store_id) REFERENCES stores(id)
        );
        """)
        run_sql(conn, """
        CREATE TABLE IF NOT EXISTS e_coupons (
            id INT AUTO_INCREMENT PRIMARY KEY,
            code VARCHAR(64) NOT NULL UNIQUE,
            amount FLOAT NOT NULL,
            customer_id INT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'available',
            payment_method VARCHAR(50) NULL,
            paid_at DATETIME NULL,
            order_id INT NULL,
            store_id INT NULL,
            redeemed_at DATETIME NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            KEY ix_ec_customer (customer_id),
            KEY ix_ec_order (order_id),
            KEY ix_ec_store (store_id),
            CONSTRAINT fk_ec_customer FOREIGN KEY (customer_id) REFERENCES customers(id),
            CONSTRAINT fk_ec_order FOREIGN KEY (order_id) REFERENCES orders(id),
            CONSTRAINT fk_ec_store FOREIGN KEY (store_id) REFERENCES stores(id)
        );
        """)
        run_sql(conn, """
        CREATE TABLE IF NOT EXISTS ad_feeds (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            body TEXT NULL,
            image_url VARCHAR(512) NULL,
            link_url VARCHAR(512) NULL,
            sort_order INT NOT NULL DEFAULT 0,
            is_active TINYINT(1) NOT NULL DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)
        run_sql(conn, """
        CREATE TABLE IF NOT EXISTS member_activities (
            id INT AUTO_INCREMENT PRIMARY KEY,
            customer_id INT NOT NULL,
            activity_type VARCHAR(50) NOT NULL,
            amount FLOAT NULL,
            description VARCHAR(255) NULL,
            ref_id INT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            KEY ix_ma_customer (customer_id),
            CONSTRAINT fk_ma_customer FOREIGN KEY (customer_id) REFERENCES customers(id)
        );
        """)
        conn.commit()

    print("Migration member_online completed.")


if __name__ == "__main__":
    main()
