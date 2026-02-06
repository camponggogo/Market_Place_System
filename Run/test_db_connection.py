"""
Test database connection (MySQL/MariaDB).
Run from project root: python Run/test_db_connection.py
"""
import sys
import os

# ให้โหลด config จาก code/
if __name__ == "__main__":
    _root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if _root not in sys.path:
        sys.path.insert(0, _root)
    _code = os.path.join(_root, "code")
    if _code not in sys.path:
        sys.path.insert(0, _code)

def main():
    from app.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, CONFIG_FILE, DATABASE_URL
    from app.database import engine

    print("=== DB Connection Test ===\n")
    print("Config (config.ini or env):")
    print(f"  CONFIG_FILE   : {CONFIG_FILE}")
    print(f"  exists        : {CONFIG_FILE.exists()}")
    print(f"  DB_HOST       : {DB_HOST}")
    print(f"  DB_PORT       : {DB_PORT}")
    print(f"  DB_NAME       : {DB_NAME}")
    print(f"  DB_USER       : {DB_USER}")
    print(f"  DB_PASSWORD   : {'*' * min(len(DB_PASSWORD or ''), 8)} (length={len(DB_PASSWORD or '')})")
    print(f"  DATABASE_URL  : mysql+pymysql://{DB_USER}:****@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4")
    print()

    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            r = conn.execute(text("SELECT 1"))
            r.fetchone()
        print("Result: OK (connected)")
        return 0
    except Exception as e:
        print("Result: FAILED")
        print(f"Error: {type(e).__name__}: {e}")
        print()
        print("Fix:")
        print("  1. Make sure MySQL/MariaDB is running")
        print("  2. Check DB_HOST, DB_PORT (e.g. localhost, 3306)")
        print("  3. Check DB_USER, DB_PASSWORD (try: mysql -u root -p)")
        print("  4. Create DB if missing: CREATE DATABASE market_place_system;")
        print("  5. If password has special chars (@ # %), they are auto-escaped")
        return 1

if __name__ == "__main__":
    sys.exit(main())
