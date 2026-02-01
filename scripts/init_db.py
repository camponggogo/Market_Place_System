"""
Script สำหรับสร้าง Database Tables และข้อมูลตัวอย่าง
"""
import sys
from pathlib import Path

# เพิ่ม root directory เข้า Python path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from app.database import engine, Base, SessionLocal
from app.models import Customer, CustomerBalance, Store
from app.config import HAS_E_MONEY_LICENSE

def init_database():
    """รัน scripts/init_db.sql เพื่อสร้าง Database และ Tables"""
    from app.config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD
    import pymysql

    sql_path = Path(__file__).parent / "init_db.sql"
    if not sql_path.exists():
        raise FileNotFoundError(f"SQL file not found: {sql_path}")

    sql_content = sql_path.read_text(encoding="utf-8")

    try:
        print(f"Connecting to MariaDB server at {DB_HOST}:{DB_PORT}...")
        connection = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            charset="utf8mb4",
        )

        # แบ่ง SQL เป็นคำสั่งทีละคำสั่ง (PyMySQL ไม่รองรับ multi=True ในบางเวอร์ชัน)
        statements = []
        current = []
        for line in sql_content.splitlines():
            current.append(line)
            if line.rstrip().endswith(";"):
                stmt = "\n".join(current).strip()
                if stmt and not stmt.strip().startswith("--"):
                    if stmt.endswith(";"):
                        stmt = stmt[:-1].strip()
                    if stmt:
                        statements.append(stmt)
                current = []
        if current:
            stmt = "\n".join(current).strip()
            if stmt and not stmt.strip().startswith("--"):
                if stmt.endswith(";"):
                    stmt = stmt[:-1].strip()
                if stmt:
                    statements.append(stmt)

        print(f"Running {sql_path.name} ({len(statements)} statements)...")
        with connection.cursor() as cursor:
            for stmt in statements:
                if stmt:
                    cursor.execute(stmt)
        connection.commit()
        connection.close()
        print("Database and tables created successfully from init_db.sql!")
    except Exception as e:
        print(f"Error running init_db.sql: {e}")
        print("Please make sure MariaDB is running and credentials are correct.")
        raise

def create_sample_data():
    """สร้างข้อมูลตัวอย่าง (ข้ามถ้ามีอยู่แล้ว)"""
    db = SessionLocal()
    try:
        # สร้างร้านค้าตัวอย่าง (ถ้ายังไม่มี)
        store = db.query(Store).filter(Store.name == "ร้านอาหารตัวอย่าง").first()
        if not store:
            store = Store(
                name="ร้านอาหารตัวอย่าง",
                tax_id="1234567890123",
                crypto_enabled=False,
                contract_accepted=False
            )
            db.add(store)
            db.commit()
            print(f"Created sample store: {store.name} (ID: {store.id})")
        else:
            print(f"Sample store already exists: {store.name} (ID: {store.id})")

        # สร้างลูกค้าตัวอย่าง (ถ้ายังไม่มี)
        customer = db.query(Customer).filter(Customer.phone == "0812345678").first()
        if not customer:
            customer = Customer(
                phone="0812345678",
                name="ลูกค้าตัวอย่าง",
                promptpay_number="0812345678"
            )
            db.add(customer)
            db.commit()
            balance = CustomerBalance(
                customer_id=customer.id,
                balance=100.00
            )
            db.add(balance)
            db.commit()
            print(f"Created sample customer: {customer.name} (ID: {customer.id}, Balance: {balance.balance})")
        else:
            print(f"Sample customer already exists: {customer.name} (ID: {customer.id})")

        print("\nSample data ready.")
        print(f"Store ID: {store.id}")
        print(f"Customer ID: {customer.id}")
        print(f"Customer Phone: {customer.phone}")

    except Exception as e:
        print(f"Error creating sample data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_database()
    create_sample_data()

