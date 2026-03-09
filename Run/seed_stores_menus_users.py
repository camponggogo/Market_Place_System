"""
Seed: สร้างข้อมูล stores, menus, users และผูก user-store สำหรับ Store POS Login
- ร้านค้า (stores) พร้อม token
- เมนู (menus) ต่อร้าน
- ราคาด่วน (store_quick_amounts) ต่อร้าน
- ผู้ใช้ pos1, pos2, ... (รหัสผ่าน pos123): pos{x} ตรงกับ store_id={x}
- admin (รหัสผ่าน admin123) is_admin=True

รันจากโฟลเดอร์โปรเจกต์:
  set PYTHONPATH=code
  python Run/seed_stores_menus_users.py

หรือจากโฟลเดอร์ code:
  python ../Run/seed_stores_menus_users.py
"""
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent / "code"
sys.path.insert(0, str(root_dir))

from app.database import SessionLocal
from app.models import Store, Menu, User, UserStore, StoreQuickAmount
from app.utils.store_token import generate_store_token

try:
    import bcrypt
    def _hash_password(pwd: str) -> str:
        return bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()
except ImportError:
    from passlib.context import CryptContext
    _pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
    def _hash_password(pwd: str) -> str:
        return _pwd.hash(pwd)


# ร้านค้าตัวอย่าง + เมนูต่อร้าน (ชื่อ, ราคา)
STORES_WITH_MENUS = [
    {
        "name": "ร้านอาหารไทย",
        "tax_id": "1234567890123",
        "menus": [
            ("ต้มยำกุ้ง", 89),
            ("ผัดไทย", 55),
            ("ข้าวผัด American", 50),
            ("แกงเขียวหวานไก่", 69),
            ("ส้มตำไทย", 49),
            ("น้ำเปล่า", 10),
            ("น้ำอัดลม", 15),
        ],
    },
    {
        "name": "ร้านก๋วยเตี๋ยว",
        "tax_id": "1234567890124",
        "menus": [
            ("ก๋วยเตี๋ยวน้ำใส", 45),
            ("ก๋วยเตี๋ยวแห้ง", 45),
            ("บะหมี่แห้ง", 50),
            ("ลูกชิ้นปลา", 10),
            ("น้ำใสเพิ่ม", 5),
        ],
    },
    {
        "name": "ร้านข้าวผัด",
        "tax_id": "1234567890125",
        "menus": [
            ("ข้าวผัดกุ้ง", 55),
            ("ข้าวผัดหมู", 50),
            ("ข้าวผัดทะเล", 65),
            ("ข้าวผัดไข่", 45),
            ("ไข่ดาว", 10),
        ],
    },
    {
        "name": "ร้านเครื่องดื่ม",
        "tax_id": "1234567890126",
        "menus": [
            ("ชาเย็น", 25),
            ("กาแฟดำ", 35),
            ("กาแฟนม", 40),
            ("น้ำส้ม", 30),
            ("สมูทตี้", 55),
        ],
    },
    {
        "name": "ร้านของหวาน",
        "tax_id": "1234567890127",
        "menus": [
            ("ขนมเค้ก", 45),
            ("ไอศกรีม", 35),
            ("ขนมปังปิ้ง", 25),
            ("บิงซู", 79),
        ],
    },
]

QUICK_AMOUNTS = [50, 100, 150, 200]  # ราคาด่วนต่อร้าน


def ensure_stores_and_menus(db):
    """สร้างร้าน + เมนู + ราคาด่วน ถ้ายังไม่มี"""
    created_stores = 0
    created_menus = 0
    created_quick = 0

    for idx, data in enumerate(STORES_WITH_MENUS, start=1):
        store = db.query(Store).filter(Store.name == data["name"]).first()
        if not store:
            store = Store(
                name=data["name"],
                tax_id=data["tax_id"],
                group_id=0,
                site_id=0,
                crypto_enabled=False,
                contract_accepted=True,
                biller_id="011556400219809",
            )
            db.add(store)
            db.flush()  # ได้ id
            store.token = generate_store_token(
                group_id=0, site_id=0, store_id=store.id, menu_id=0
            )
            db.commit()
            db.refresh(store)
            created_stores += 1
            print(f"  สร้างร้าน: {store.name} (id={store.id}, token={store.token})")
        else:
            if not store.token:
                store.token = generate_store_token(
                    group_id=getattr(store, "group_id", 0) or 0,
                    site_id=getattr(store, "site_id", 0) or 0,
                    store_id=store.id,
                    menu_id=0,
                )
                db.commit()
                db.refresh(store)

        # เมนูของร้านนี้
        existing_menus = db.query(Menu).filter(Menu.store_id == store.id).count()
        if existing_menus == 0:
            for order, (menu_name, price) in enumerate(data["menus"], start=1):
                m = Menu(
                    store_id=store.id,
                    name=menu_name,
                    unit_price=float(price),
                    is_active=True,
                )
                db.add(m)
                created_menus += 1
            db.commit()
            print(f"  สร้างเมนู {len(data['menus'])} รายการให้ร้าน {store.name}")

        # ราคาด่วน
        existing_quick = db.query(StoreQuickAmount).filter(
            StoreQuickAmount.store_id == store.id
        ).count()
        if existing_quick == 0:
            for i, amt in enumerate(QUICK_AMOUNTS):
                q = StoreQuickAmount(
                    store_id=store.id,
                    amount=float(amt),
                    label=f"{amt} บาท",
                    display_order=i + 1,
                    is_active=True,
                )
                db.add(q)
                created_quick += 1
            db.commit()
            print(f"  สร้างราคาด่วน {len(QUICK_AMOUNTS)} รายการให้ร้าน {store.name}")

    return created_stores, created_menus, created_quick


def ensure_pos_users(db):
    """สร้าง user pos{x} รหัสผ่าน pos123 และผูกกับ store_id=x (pos1->store_id=1, pos2->store_id=2, ...)"""
    stores = db.query(Store).order_by(Store.id).all()
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
        # ผูก user กับร้าน store_id=sid (ถ้ายังไม่มี)
        link = (
            db.query(UserStore)
            .filter(UserStore.user_id == user.id, UserStore.store_id == sid)
            .first()
        )
        if not link:
            db.add(UserStore(user_id=user.id, store_id=sid))
            db.commit()
            print(f"  ผูก {username} -> ร้าน {store.name} (store_id={sid})")
    return created


def ensure_admin(db):
    """สร้างหรืออัปเดต admin"""
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
        print("  สร้าง admin: username=admin, รหัสผ่าน admin123, is_admin=True")
        return 1
    if not getattr(admin, "is_admin", False):
        admin.is_admin = True
        db.commit()
        print("  อัปเดต admin: set is_admin=True")
    return 0


def main():
    print("Seed: stores + menus + quick amounts + users (Store POS login)")
    print("=" * 60)
    db = SessionLocal()
    try:
        print("\n[1] ร้านค้า + เมนู + ราคาด่วน")
        s, m, q = ensure_stores_and_menus(db)
        print(f"    สร้างร้าน {s} ร้าน, เมนู {m} รายการ, ราคาด่วน {q} รายการ\n")

        print("[2] ผู้ใช้ Store POS (pos1, pos2, ... รหัสผ่าน pos123) + ผูกร้าน")
        u = ensure_pos_users(db)
        print(f"    สร้าง user ใหม่ {u} คน\n")

        print("[3] Admin (admin / admin123)")
        ensure_admin(db)

        print("\n" + "=" * 60)
        print("เสร็จแล้ว — pos1/pos123 = store_id=1, pos2/pos123 = store_id=2, ... (user pos{x} ตรงกับ store_id={x})")
    finally:
        db.close()


if __name__ == "__main__":
    main()
