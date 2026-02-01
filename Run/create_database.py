"""
Script สำหรับสร้าง Database ใน MariaDB
"""
import sys
from pathlib import Path

# โปรเจกต์จัดเป็น code/ + Run/ + Deploy/
root_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(root_dir))

from app.config import DB_NAME, DB_HOST, DB_PORT, DB_USER, DB_PASSWORD
import pymysql

def create_database():
    """สร้าง Database ใน MariaDB"""
    try:
        print(f"Connecting to MariaDB server at {DB_HOST}:{DB_PORT}...")
        connection = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            # ตรวจสอบว่า database มีอยู่แล้วหรือไม่
            cursor.execute(f"SHOW DATABASES LIKE '{DB_NAME}'")
            result = cursor.fetchone()
            
            if not result:
                print(f"Creating database '{DB_NAME}'...")
                cursor.execute(f"CREATE DATABASE {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                connection.commit()
                print(f"✅ Database '{DB_NAME}' created successfully!")
            else:
                print(f"ℹ️  Database '{DB_NAME}' already exists.")
        
        connection.close()
        return True
    except pymysql.Error as e:
        print(f"❌ Error: {e}")
        print("\nPlease check:")
        print(f"  1. MariaDB is running")
        print(f"  2. Host: {DB_HOST}")
        print(f"  3. Port: {DB_PORT}")
        print(f"  4. User: {DB_USER}")
        print(f"  5. Password is correct")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = create_database()
    if success:
        print("\n✅ Database setup complete!")
        print("Next step: Run 'python scripts/init_db.py' to create tables")
    else:
        print("\n❌ Database setup failed!")
        sys.exit(1)

