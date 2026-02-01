"""
Script สำหรับตรวจสอบการตั้งค่าและ dependencies
"""
import sys
from pathlib import Path

# โปรเจกต์จัดเป็น code/ + Run/ + Deploy/
root_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(root_dir))

def check_dependencies():
    """ตรวจสอบ dependencies"""
    print("=" * 60)
    print("Checking Dependencies...")
    print("=" * 60)
    
    required_packages = {
        "fastapi": "FastAPI",
        "uvicorn": "Uvicorn",
        "sqlalchemy": "SQLAlchemy",
        "pymysql": "PyMySQL",
        "pydantic": "Pydantic",
        "aiohttp": "aiohttp",
        "qrcode": "qrcode",
        "PIL": "Pillow",
        "pandas": "pandas",
        "schedule": "schedule"
    }
    
    missing_packages = []
    
    for package, name in required_packages.items():
        try:
            __import__(package)
            print(f"✅ {name} - OK")
        except ImportError:
            print(f"❌ {name} - MISSING")
            missing_packages.append(name)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Run: pip install -r requirements.txt")
        return False
    else:
        print("\n✅ All required packages are installed!")
        return True

def check_config():
    """ตรวจสอบไฟล์ config"""
    print("\n" + "=" * 60)
    print("Checking Configuration...")
    print("=" * 60)
    
    config_file = root_dir / "config.ini"
    
    if not config_file.exists():
        print("❌ config.ini not found!")
        return False
    
    print("✅ config.ini exists")
    
    try:
        import configparser
        config = configparser.ConfigParser()
        config.read(config_file)
        
        # ตรวจสอบ sections
        required_sections = ["DATABASE", "BACKEND", "E_MONEY", "CRYPTO", "TAX", "PAYMENT", "NOTIFICATION"]
        for section in required_sections:
            if config.has_section(section):
                print(f"✅ [{section}] section exists")
            else:
                print(f"❌ [{section}] section missing")
                return False
        
        # ตรวจสอบ database settings
        db_host = config.get("DATABASE", "DB_HOST", fallback=None)
        db_port = config.getint("DATABASE", "DB_PORT", fallback=None)
        db_name = config.get("DATABASE", "DB_NAME", fallback=None)
        db_user = config.get("DATABASE", "DB_USER", fallback=None)
        
        print(f"\nDatabase Settings:")
        print(f"  Host: {db_host}")
        print(f"  Port: {db_port}")
        print(f"  Database: {db_name}")
        print(f"  User: {db_user}")
        
        return True
    except Exception as e:
        print(f"❌ Error reading config: {e}")
        return False

def check_database_connection():
    """ตรวจสอบการเชื่อมต่อ database"""
    print("\n" + "=" * 60)
    print("Checking Database Connection...")
    print("=" * 60)
    
    try:
        from app.config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
        import pymysql
        
        print(f"Connecting to MariaDB at {DB_HOST}:{DB_PORT}...")
        connection = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            # ตรวจสอบ database
            cursor.execute(f"SHOW DATABASES LIKE '{DB_NAME}'")
            result = cursor.fetchone()
            
            if result:
                print(f"✅ Database '{DB_NAME}' exists")
            else:
                print(f"⚠️  Database '{DB_NAME}' not found")
                print(f"   Run: PYTHONPATH=code python Run/create_database.py")
                connection.close()
                return False
        
        connection.close()
        print("✅ Database connection successful!")
        return True
    except pymysql.Error as e:
        print(f"❌ Database connection failed: {e}")
        print("   Please check:")
        print("   1. MariaDB is running")
        print("   2. Database credentials in config.ini")
        return False
    except ImportError:
        print("❌ PyMySQL not installed")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def check_files():
    """ตรวจสอบไฟล์สำคัญ"""
    print("\n" + "=" * 60)
    print("Checking Important Files...")
    print("=" * 60)
    
    required_files = [
        "main.py",
        "app/__init__.py",
        "app/config.py",
        "app/database.py",
        "app/models.py",
        "app/api/__init__.py",
        "app/services/__init__.py",
        "config.ini",
        "requirements.txt"
    ]
    
    missing_files = []
    
    for file_path in required_files:
        full_path = root_dir / file_path
        if full_path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - MISSING")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n⚠️  Missing files: {', '.join(missing_files)}")
        return False
    else:
        print("\n✅ All required files exist!")
        return True

def check_api_modules():
    """ตรวจสอบ API modules"""
    print("\n" + "=" * 60)
    print("Checking API Modules...")
    print("=" * 60)
    
    api_modules = [
        "app.api.customer",
        "app.api.crypto",
        "app.api.reports",
        "app.api.tax",
        "app.api.refund",
        "app.api.stores",
        "app.api.counter",
        "app.api.payment_hub",
        "app.api.reports_payment"
    ]
    
    missing_modules = []
    
    for module in api_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module} - {e}")
            missing_modules.append(module)
    
    if missing_modules:
        print(f"\n⚠️  Missing modules: {len(missing_modules)}")
        return False
    else:
        print("\n✅ All API modules can be imported!")
        return True

def main():
    """Main function"""
    print("\n" + "=" * 60)
    print("Food Court Management System - Setup Checker")
    print("=" * 60 + "\n")
    
    results = {
        "Dependencies": check_dependencies(),
        "Configuration": check_config(),
        "Files": check_files(),
        "API Modules": check_api_modules(),
        "Database": check_database_connection()
    }
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    all_ok = True
    for check, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{check}: {status}")
        if not result:
            all_ok = False
    
    print("\n" + "=" * 60)
    if all_ok:
        print("✅ All checks passed! System is ready.")
        print("\nNext steps:")
        print("  1. Run: PYTHONPATH=code python Run/init_db.py")
        print("  2. Run: uvicorn main:app --reload")
    else:
        print("⚠️  Some checks failed. Please fix the issues above.")
    print("=" * 60 + "\n")
    
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())

