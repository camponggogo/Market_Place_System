"""
Seed: สร้างสมาชิก (Customer) ตัวอย่างสำหรับระบบ Member
- สมาชิกออนไลน์ (username, phone, password, email, name)
- สร้าง CustomerBalance ให้แต่ละคน

ถ้า DB ยังไม่มีคอลัมน์ username/email/password_hash ในตาราง customers ให้รัน migration ก่อน (ไม่ต้องมีโปรแกรม mysql):
  python Run/run_migrations.py

รันจากโฟลเดอร์โปรเจกต์:
  set PYTHONPATH=code
  python Run/seed_members.py

ตัวอย่างบัญชีหลังรัน:
  member1 / 0811111111 / member123
  member2 / 0822222222 / member123
  demo    / 0899999999 / demo1234
"""
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent / "code"
sys.path.insert(0, str(root_dir))

from app.database import SessionLocal
from app.models import Customer, CustomerBalance

try:
    import bcrypt
    def _hash_password(pwd: str) -> str:
        return bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()
except ImportError:
    from passlib.context import CryptContext
    _pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
    def _hash_password(pwd: str) -> str:
        return _pwd.hash(pwd)


# สมาชิกตัวอย่าง: (username, phone, password, email, name)
MEMBERS = [
    ("member1", "0811111111", "member123", "member1@example.com", "สมาชิกหนึ่ง"),
    ("member2", "0822222222", "member123", "member2@example.com", "สมาชิกสอง"),
    ("demo", "0899999999", "demo1234", "demo@example.com", "Demo User"),
    ("testuser", "0888888888", "test1234", None, "ผู้ใช้ทดสอบ"),
]


def ensure_members(db):
    """สร้างสมาชิกตัวอย่างและ balance ถ้ายังไม่มี"""
    created = 0
    for username, phone, password, email, name in MEMBERS:
        if db.query(Customer).filter(Customer.username == username).first():
            print(f"  ข้าม (มีแล้ว): {username}")
            continue
        if db.query(Customer).filter(Customer.phone == phone).first():
            print(f"  ข้าม (เบอร์ซ้ำ): {phone}")
            continue
        customer = Customer(
            username=username,
            phone=phone,
            email=email,
            name=name,
            password_hash=_hash_password(password),
            total_points=0.0,
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)
        balance = CustomerBalance(customer_id=customer.id, balance=0.0)
        db.add(balance)
        db.commit()
        created += 1
        pwd_note = "รหัสผ่าน " + password
        print(f"  สร้างสมาชิก: {username} / {phone} / {pwd_note}")
    return created


def main():
    print("Seed: สมาชิก (Member) ตัวอย่าง")
    print("=" * 60)
    db = SessionLocal()
    try:
        n = ensure_members(db)
        print(f"\nสร้างสมาชิกใหม่ {n} คน")
        print("=" * 60)
        print("ใช้เข้าสู่ระบบที่ /member ได้ดังนี้:")
        for username, phone, password, _e, _n in MEMBERS:
            print(f"  {username} หรือ {phone} / รหัสผ่าน: {password}")
    except Exception as e:
        err = str(e)
        if "Unknown column" in err and "customers" in err:
            print("\n[!] ตาราง customers ยังไม่มีคอลัมน์สำหรับ Member (username, email, password_hash)")
            print("    รัน migration ก่อน (ใช้ config.ini ไม่ต้องมีโปรแกรม mysql):")
            print("      python Run/run_migrations.py")
            sys.exit(1)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
