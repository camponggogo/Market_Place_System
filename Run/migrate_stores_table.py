"""
Migration script to add new columns to stores table
"""
import sys
from pathlib import Path

# เพิ่ม root directory เข้า Python path
root_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(root_dir))

from app.config import DB_NAME, DB_HOST, DB_PORT, DB_USER, DB_PASSWORD
import pymysql

def migrate_stores_table():
    """เพิ่ม columns ใหม่ใน stores table"""
    try:
        print(f"Connecting to MariaDB server at {DB_HOST}:{DB_PORT}...")
        connection = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            # ตรวจสอบว่า columns มีอยู่แล้วหรือไม่
            cursor.execute("SHOW COLUMNS FROM stores LIKE 'latitude'")
            has_latitude = cursor.fetchone()
            
            if not has_latitude:
                print("Adding new columns to stores table...")
                
                # เพิ่ม columns ใหม่
                cursor.execute("""
                    ALTER TABLE stores 
                    ADD COLUMN latitude FLOAT NULL,
                    ADD COLUMN longitude FLOAT NULL,
                    ADD COLUMN location_name VARCHAR(255) NULL,
                    ADD COLUMN profile_id INT NULL,
                    ADD COLUMN event_id INT NULL
                """)
                
                # เพิ่ม foreign keys ถ้า tables มีอยู่
                try:
                    cursor.execute("SHOW TABLES LIKE 'profiles'")
                    if cursor.fetchone():
                        cursor.execute("""
                            ALTER TABLE stores 
                            ADD CONSTRAINT fk_stores_profile 
                            FOREIGN KEY (profile_id) REFERENCES profiles(id)
                        """)
                except Exception as e:
                    print(f"Warning: Could not add profile foreign key: {e}")
                
                try:
                    cursor.execute("SHOW TABLES LIKE 'events'")
                    if cursor.fetchone():
                        cursor.execute("""
                            ALTER TABLE stores 
                            ADD CONSTRAINT fk_stores_event 
                            FOREIGN KEY (event_id) REFERENCES events(id)
                        """)
                except Exception as e:
                    print(f"Warning: Could not add event foreign key: {e}")
                
                connection.commit()
                print("✅ Successfully added new columns to stores table!")
            else:
                print("✅ Columns already exist in stores table")
        
        connection.close()
        return True
    except Exception as e:
        print(f"❌ Error migrating stores table: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Migrating stores table...")
    print("=" * 60)
    migrate_stores_table()

