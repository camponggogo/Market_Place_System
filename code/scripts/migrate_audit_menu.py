"""
Migration: audit_logs.source, menu_price_logs สำหรับเก็บราคาเดิมและ log การดำเนินการ
รัน: python scripts/migrate_audit_menu.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text
from app.database import engine


def run_sql(conn, sql: str):
    for stmt in (s.strip() for s in sql.strip().split(";") if s.strip() and not s.strip().startswith("--")):
        if stmt:
            conn.execute(text(stmt))


def main():
    with engine.connect() as conn:
        # audit_logs: เพิ่ม source
        try:
            conn.execute(text("ALTER TABLE audit_logs ADD COLUMN source VARCHAR(50) NULL"))
            conn.commit()
        except Exception:
            conn.rollback()
            pass

        # users: is_admin
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN is_admin TINYINT(1) NOT NULL DEFAULT 0"))
            conn.commit()
        except Exception:
            conn.rollback()
            pass

        # emergency_backup_entries
        run_sql(conn, """
        CREATE TABLE IF NOT EXISTS emergency_backup_entries (
            id INT AUTO_INCREMENT PRIMARY KEY,
            source VARCHAR(20) NOT NULL,
            store_id INT NULL,
            entry_type VARCHAR(50) NOT NULL,
            amount FLOAT NOT NULL,
            description TEXT NULL,
            entered_by_user_id INT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            KEY ix_ebe_source (source),
            KEY ix_ebe_store (store_id),
            KEY ix_ebe_entered (entered_by_user_id),
            CONSTRAINT fk_ebe_store FOREIGN KEY (store_id) REFERENCES stores(id),
            CONSTRAINT fk_ebe_user FOREIGN KEY (entered_by_user_id) REFERENCES users(id)
        );
        """)

        # menu_price_logs
        run_sql(conn, """
        CREATE TABLE IF NOT EXISTS menu_price_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            menu_id INT NOT NULL,
            unit_price FLOAT NOT NULL,
            addon_options_json TEXT NULL,
            effective_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            changed_by_user_id INT NULL,
            KEY ix_mpl_menu (menu_id),
            CONSTRAINT fk_mpl_menu FOREIGN KEY (menu_id) REFERENCES menus(id)
        );
        """)
        # ad_feeds: store_id, start_at, end_at (เลือกร้าน, ตั้งเวลาปล่อย)
        for col, defn in [
            ("store_id", "INT NULL"),
            ("start_at", "DATETIME NULL"),
            ("end_at", "DATETIME NULL"),
        ]:
            try:
                conn.execute(text(f"ALTER TABLE ad_feeds ADD COLUMN {col} {defn}"))
                conn.commit()
            except Exception:
                conn.rollback()
                pass
        # ad_feeds: media_type, video_url (รองรับ video หรือภาพ slide)
        for col, defn in [
            ("media_type", "VARCHAR(20) NOT NULL DEFAULT 'image'"),
            ("video_url", "VARCHAR(512) NULL"),
        ]:
            try:
                conn.execute(text(f"ALTER TABLE ad_feeds ADD COLUMN {col} {defn}"))
                conn.commit()
            except Exception:
                conn.rollback()
                pass
        # ad_feeds: delivery_mode (stream | download)
        try:
            conn.execute(text("ALTER TABLE ad_feeds ADD COLUMN delivery_mode VARCHAR(20) NOT NULL DEFAULT 'stream'"))
            conn.commit()
        except Exception:
            conn.rollback()
            pass
        # promptpay_back_transactions: payment_gateway (stripe, omise, ฯลฯ สำหรับ Report)
        try:
            conn.execute(text("ALTER TABLE promptpay_back_transactions ADD COLUMN payment_gateway VARCHAR(30) NULL"))
            conn.commit()
        except Exception:
            conn.rollback()
            pass

        # ad_impressions สำหรับสรุปผลการตอบรับโฆษณา
        run_sql(conn, """
        CREATE TABLE IF NOT EXISTS ad_impressions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            ad_feed_id INT NOT NULL,
            event_type VARCHAR(20) NOT NULL,
            customer_id INT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            KEY ix_ai_ad (ad_feed_id),
            KEY ix_ai_created (created_at),
            CONSTRAINT fk_ai_ad FOREIGN KEY (ad_feed_id) REFERENCES ad_feeds(id),
            CONSTRAINT fk_ai_customer FOREIGN KEY (customer_id) REFERENCES customers(id)
        );
        """)
        conn.commit()
    print("Migration audit_menu completed.")


if __name__ == "__main__":
    main()
