"""
ดาวน์โหลดรูปจาก Internet → แปลงเป็น base64 → บันทึกลง database (menus.image_base64)

วิธีใช้:
  python scripts/fetch_image_to_base64.py <menu_id> <image_url>
  python scripts/fetch_image_to_base64.py 1 https://example.com/food.jpg

หรือระบุหลายเมนู:
  python scripts/fetch_image_to_base64.py 1 https://url1.jpg 2 https://url2.jpg
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.models import Menu
from app.services.menu_image_service import download_and_save


def main():
    args = sys.argv[1:]
    if len(args) < 2 or len(args) % 2 != 0:
        print("วิธีใช้: python fetch_image_to_base64.py <menu_id> <image_url> [menu_id url ...]")
        print("ตัวอย่าง: python fetch_image_to_base64.py 1 https://example.com/food.jpg")
        return 1

    db = SessionLocal()
    try:
        i = 0
        while i < len(args):
            menu_id = int(args[i])
            image_url = args[i + 1].strip()
            i += 2

            menu = db.query(Menu).filter(Menu.id == menu_id).first()
            if not menu:
                print(f"  [ข้าม] ไม่พบเมนู ID {menu_id}")
                continue

            print(f"  เมนู #{menu_id} ({menu.name}) <- {image_url[:60]}...")
            local_path, b64, err = download_and_save(image_url, menu.store_id, menu.id)
            if err and not b64:
                print(f"    ❌ ล้มเหลว: {err}")
                continue

            menu.image_base64 = b64
            if local_path:
                menu.image_local = local_path
            if not menu.image_url:
                menu.image_url = image_url
            db.commit()
            print(f"    ✅ บันทึก base64 แล้ว" + (f" (local: {local_path})" if local_path else ""))
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
