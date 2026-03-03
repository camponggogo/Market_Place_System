"""
Seed: สร้าง user ตัวอย่างสำหรับ Store POS Login
- username: pos1
- password: pos123
- สิทธิ์เข้าถึง store_id=1

รัน: python scripts/seed_store_pos_user.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.models import User, UserStore

try:
    import bcrypt
    def _hash_password(pwd: str) -> str:
        return bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()
except ImportError:
    from passlib.context import CryptContext
    _pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
    def _hash_password(pwd: str) -> str:
        return _pwd.hash(pwd)


def main():
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == "pos1").first()
        if not existing:
            user = User(
                username="pos1",
                password_hash=_hash_password("pos123"),
                name="พนักงานร้าน 1",
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            us = UserStore(user_id=user.id, store_id=1)
            db.add(us)
            db.commit()
            print("Created user: username=pos1, password=pos123, store_id=1")
        else:
            print("User pos1 already exists")

        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin = User(
                username="admin",
                password_hash=_hash_password("admin123"),
                name="ผู้ดูแลระบบ",
                is_admin=True,
            )
            db.add(admin)
            db.commit()
            print("Created admin user: username=admin, password=admin123, is_admin=True")
        else:
            if not getattr(admin, "is_admin", False):
                admin.is_admin = True
                db.commit()
                print("Updated existing admin user: set is_admin=True")
    finally:
        db.close()


if __name__ == "__main__":
    main()
