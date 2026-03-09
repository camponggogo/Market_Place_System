"""
รัน migration SQL กับ DB ตาม config.ini (ไม่ต้องมี mysql ใน PATH)
ใช้: python Run/run_migrations.py
หรือ: cd Run && python run_migrations.py
"""
import sys
import os

# โหลด config จาก code/config.ini
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CODE = os.path.join(BASE, "code")
CONFIG_PATH = os.path.join(CODE, "config.ini")
if not os.path.isfile(CONFIG_PATH):
    print("ไม่พบ code/config.ini")
    sys.exit(1)

import configparser
config = configparser.ConfigParser()
config.read(CONFIG_PATH, encoding="utf-8")

db_host = os.environ.get("DB_HOST") or config.get("DATABASE", "DB_HOST", fallback="localhost")
db_port = int(os.environ.get("DB_PORT") or config.get("DATABASE", "DB_PORT", fallback="3306"))
db_name = os.environ.get("DB_NAME") or config.get("DATABASE", "DB_NAME", fallback="market_place_system")
db_user = os.environ.get("DB_USER") or config.get("DATABASE", "DB_USER", fallback="root")
db_pass = os.environ.get("DB_PASSWORD") or config.get("DATABASE", "DB_PASSWORD", fallback="123456")

try:
    import pymysql
except ImportError:
    print("ติดตั้ง pymysql ก่อน: pip install pymysql")
    sys.exit(1)


def run_sql(conn, sql, desc):
    """รัน SQL เดียว; ข้ามถ้า column มีอยู่แล้ว (Duplicate column)"""
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
        print("  OK:", desc)
        return True
    except pymysql.err.OperationalError as e:
        errno = e.args[0] if e.args else 0
        if errno == 1060:  # Duplicate column name
            print("  ข้าม (column มีอยู่แล้ว):", desc)
            return False
        if errno == 1061:  # Duplicate key name
            print("  ข้าม (index มีอยู่แล้ว):", desc)
            return False
        raise
    except Exception as e:
        conn.rollback()
        raise


def main():
    print("เชื่อมต่อ DB:", db_host, "port", db_port, "database", db_name)
    conn = pymysql.connect(
        host=db_host,
        port=db_port,
        user=db_user,
        password=db_pass,
        database=db_name,
        charset="utf8mb4",
    )
    try:
        print("\nรัน migrations:")
        # 1) users.is_admin
        run_sql(
            conn,
            "ALTER TABLE `users` ADD COLUMN `is_admin` tinyint(1) NOT NULL DEFAULT 0 AFTER `name`",
            "users.is_admin",
        )
        # 2) promptpay_back_transactions.payment_gateway
        run_sql(
            conn,
            "ALTER TABLE `promptpay_back_transactions` ADD COLUMN `payment_gateway` varchar(30) DEFAULT NULL AFTER `status`",
            "promptpay_back_transactions.payment_gateway",
        )
        run_sql(
            conn,
            "ALTER TABLE `promptpay_back_transactions` ADD KEY `ix_promptpay_back_transactions_payment_gateway` (`payment_gateway`)",
            "promptpay_back_transactions index payment_gateway",
        )
        # 3) stores: คอลัมน์ SCB / K Bank / bank_account / name_i18n (ให้ตรงกับ model)
        run_sql(conn, "ALTER TABLE `stores` ADD COLUMN `name_i18n` text DEFAULT NULL AFTER `name`", "stores.name_i18n")
        run_sql(conn, "ALTER TABLE `stores` ADD COLUMN `scb_app_name` varchar(64) DEFAULT NULL AFTER `event_id`", "stores.scb_app_name")
        run_sql(conn, "ALTER TABLE `stores` ADD COLUMN `scb_api_key` varchar(128) DEFAULT NULL AFTER `scb_app_name`", "stores.scb_api_key")
        run_sql(conn, "ALTER TABLE `stores` ADD COLUMN `scb_api_secret` varchar(255) DEFAULT NULL AFTER `scb_api_key`", "stores.scb_api_secret")
        run_sql(conn, "ALTER TABLE `stores` ADD COLUMN `scb_callback_url` varchar(512) DEFAULT NULL AFTER `scb_api_secret`", "stores.scb_callback_url")
        run_sql(conn, "ALTER TABLE `stores` ADD COLUMN `kbank_customer_id` varchar(128) DEFAULT NULL AFTER `scb_callback_url`", "stores.kbank_customer_id")
        run_sql(conn, "ALTER TABLE `stores` ADD COLUMN `kbank_consumer_secret` varchar(255) DEFAULT NULL AFTER `kbank_customer_id`", "stores.kbank_consumer_secret")
        run_sql(conn, "ALTER TABLE `stores` ADD COLUMN `bank_account` varchar(50) DEFAULT NULL AFTER `kbank_consumer_secret`", "stores.bank_account")
        run_sql(conn, "ALTER TABLE `stores` ADD COLUMN `bank_name` varchar(128) DEFAULT NULL AFTER `bank_account`", "stores.bank_name")
        run_sql(conn, "ALTER TABLE `stores` ADD COLUMN `bank_branch` varchar(128) DEFAULT NULL AFTER `bank_name`", "stores.bank_branch")
        # 4) menus: คอลัมน์ให้ตรงกับ model (name_i18n, description_i18n, image_*, barcode, addon_options)
        run_sql(conn, "ALTER TABLE `menus` ADD COLUMN `name_i18n` text DEFAULT NULL AFTER `name`", "menus.name_i18n")
        run_sql(conn, "ALTER TABLE `menus` ADD COLUMN `description_i18n` text DEFAULT NULL AFTER `description`", "menus.description_i18n")
        run_sql(conn, "ALTER TABLE `menus` ADD COLUMN `image_url` varchar(512) DEFAULT NULL AFTER `unit_price`", "menus.image_url")
        run_sql(conn, "ALTER TABLE `menus` ADD COLUMN `image_local` varchar(255) DEFAULT NULL AFTER `image_url`", "menus.image_local")
        run_sql(conn, "ALTER TABLE `menus` ADD COLUMN `image_base64` mediumtext DEFAULT NULL AFTER `image_local`", "menus.image_base64")
        run_sql(conn, "ALTER TABLE `menus` ADD COLUMN `barcode` varchar(64) DEFAULT NULL AFTER `image_base64`", "menus.barcode")
        run_sql(conn, "ALTER TABLE `menus` ADD COLUMN `addon_options` text DEFAULT NULL AFTER `barcode`", "menus.addon_options")
        run_sql(conn, "ALTER TABLE `menus` ADD KEY `ix_menus_barcode` (`barcode`)", "menus index barcode")
        # 5) customers: คอลัมน์ Member (username, email, password_hash, total_points, updated_at)
        run_sql(conn, "ALTER TABLE `customers` ADD COLUMN `username` varchar(64) DEFAULT NULL AFTER `promptpay_number`", "customers.username")
        run_sql(conn, "ALTER TABLE `customers` ADD COLUMN `email` varchar(255) DEFAULT NULL AFTER `username`", "customers.email")
        run_sql(conn, "ALTER TABLE `customers` ADD COLUMN `password_hash` varchar(255) DEFAULT NULL AFTER `email`", "customers.password_hash")
        run_sql(conn, "ALTER TABLE `customers` ADD COLUMN `total_points` float NOT NULL DEFAULT 0 AFTER `password_hash`", "customers.total_points")
        run_sql(conn, "ALTER TABLE `customers` ADD COLUMN `updated_at` datetime DEFAULT NULL ON UPDATE current_timestamp() AFTER `created_at`", "customers.updated_at")
        run_sql(conn, "ALTER TABLE `customers` ADD UNIQUE KEY `ix_customers_username` (`username`)", "customers unique ix_customers_username")
        run_sql(conn, "ALTER TABLE `customers` ADD UNIQUE KEY `ix_customers_email` (`email`)", "customers unique ix_customers_email")
        print("\nเสร็จแล้ว")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
