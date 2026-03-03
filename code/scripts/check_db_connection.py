"""
ตรวจสอบการเชื่อมต่อ Database
รัน: python scripts/check_db_connection.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

def check():
    from app.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, DATABASE_URL
    print("=== Database Configuration ===")
    print(f"  Host:     {DB_HOST}")
    print(f"  Port:     {DB_PORT}")
    print(f"  Database: {DB_NAME}")
    print(f"  User:     {DB_USER}")
    print(f"  Password: {'*' * len(DB_PASSWORD) if DB_PASSWORD else '(empty)'}")
    print(f"  URL:      mysql+pymysql://{DB_USER}:****@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4")
    print()

    # 1. Check pymysql
    try:
        import pymysql
        print("[OK] pymysql installed:", pymysql.__version__)
    except ImportError:
        print("[FAIL] pymysql not installed. Run: pip install pymysql")
        return False

    # 2. Try raw connection (without DB)
    try:
        conn = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            connect_timeout=5
        )
        conn.close()
        print("[OK] MySQL server reachable (without database)")
    except pymysql.Error as e:
        print(f"[FAIL] Cannot connect to MySQL: {e}")
        print("  - ตรวจสอบว่า MySQL/MariaDB กำลังรันอยู่")
        print("  - ตรวจสอบ DB_HOST, DB_PORT ใน config.ini")
        return False

    # 3. Check database exists
    try:
        conn = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            connect_timeout=5
        )
        conn.close()
        print(f"[OK] Database '{DB_NAME}' exists and accessible")
    except pymysql.Error as e:
        print(f"[FAIL] Cannot access database '{DB_NAME}': {e}")
        print("  - รัน Run\\seed_full_sample.ps1 เพื่อสร้าง database")
        return False

    # 4. Try SQLAlchemy engine
    try:
        from sqlalchemy import text
        from app.database import engine
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("[OK] SQLAlchemy engine connection works")
    except Exception as e:
        print(f"[FAIL] SQLAlchemy: {e}")
        return False

    # 5. Check key tables
    try:
        from sqlalchemy import text
        from app.database import engine
        tables = ["stores", "menus", "program_settings", "translations"]
        with engine.connect() as conn:
            for t in tables:
                try:
                    conn.execute(text(f"SELECT 1 FROM {t} LIMIT 1"))
                    print(f"[OK] Table '{t}' exists")
                except Exception:
                    print(f"[--] Table '{t}' missing (อาจต้องรัน migration)")
    except Exception as e:
        print(f"[WARN] Table check: {e}")

    print()
    print("=== Summary: Database connection OK ===")
    return True

if __name__ == "__main__":
    ok = check()
    sys.exit(0 if ok else 1)
