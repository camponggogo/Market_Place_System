"""
Migration: สร้างตาราง store_locale_settings สำหรับจดจำภาษาต่อร้าน
รันครั้งเดียว: python scripts/migrate_store_locale_settings.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import engine
from app.models import Base, StoreLocaleSetting

Base.metadata.create_all(bind=engine, tables=[StoreLocaleSetting.__table__])
print("Migration: store_locale_settings done")
