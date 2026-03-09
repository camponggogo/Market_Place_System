"""
อัปเดต user Store POS: สร้าง/ผูก pos{x} กับ store_id=x (รหัสผ่าน pos123)
- pos1 -> store_id=1, pos2 -> store_id=2, ...
รันเมื่อเพิ่มร้านใหม่หรือต้องการ sync user กับร้าน

  set PYTHONPATH=code
  python Run/update_pos_users.py
"""
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent / "code"
sys.path.insert(0, str(root_dir))

from app.database import SessionLocal
from app.models import Store, User, UserStore

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
        stores = db.query(Store).order_by(Store.id).all()
        if not stores:
            print("ยังไม่มีร้านในระบบ — รัน seed_stores_menus_users.py ก่อน")
            return
        created = 0
        for store in stores:
            sid = store.id
            username = f"pos{sid}"
            user = db.query(User).filter(User.username == username).first()
            if not user:
                user = User(
                    username=username,
                    password_hash=_hash_password("pos123"),
                    name=f"พนักงานร้าน {store.name}",
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                created += 1
                print(f"  สร้าง user: {username} (รหัสผ่าน pos123) -> store_id={sid}")
            link = (
                db.query(UserStore)
                .filter(UserStore.user_id == user.id, UserStore.store_id == sid)
                .first()
            )
            if not link:
                db.add(UserStore(user_id=user.id, store_id=sid))
                db.commit()
                print(f"  ผูก {username} -> ร้าน {store.name} (store_id={sid})")
        print(f"\nเสร็จ — pos{{x}} ตรงกับ store_id={{x}}, รหัสผ่าน pos123 (สร้าง user ใหม่ {created} คน)")
    finally:
        db.close()


if __name__ == "__main__":
    main()
