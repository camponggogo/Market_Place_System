"""
Menu API - ระบบจัดการรายการสินค้า (เก็บราคาเดิมใน menu_price_logs เมื่อแก้ไข)
"""
import json
from pathlib import Path
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import BACKEND_URL
from app.database import get_db
from app.models import Menu, Store, MenuPriceLog
from app.services.menu_image_service import MENU_IMAGES_DIR, download_and_save, fetch_url_to_base64
from app.services.audit_log import write_audit_log
from app.utils.i18n import resolve_i18n, resolve_addon_options

router = APIRouter(prefix="/api/menus", tags=["menus"])

_POS_SETTINGS_FILE = Path(__file__).resolve().parent.parent / "data" / "pos_settings.json"


def _get_menu_image_priority() -> str:
    """อ่านลำดับการเลือกแหล่งรูปจาก pos_settings"""
    default = "local,server,base64"
    if not _POS_SETTINGS_FILE.exists():
        return default
    try:
        with open(_POS_SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("menu_image_priority", default)
    except Exception:
        return default


def _resolve_image_src(menu: Menu, base_url: str) -> Optional[str]:
    """
    คืนค่า URL หรือ data URI ของรูปตามลำดับ menu_image_priority
    - local: /menu-images/{filename} ถ้ามีไฟล์
    - server: image_url
    - base64: data:image/jpeg;base64,...
    """
    priority = _get_menu_image_priority()
    parts = [p.strip().lower() for p in priority.split(",") if p.strip()]
    base = (base_url or BACKEND_URL or "").rstrip("/")

    for src in parts:
        if src == "local":
            fl = getattr(menu, "image_local", None)
            if fl and (MENU_IMAGES_DIR / fl).exists():
                return f"{base}/menu-images/{fl}"
        elif src == "server":
            url = getattr(menu, "image_url", None)
            if url and url.strip():
                return url.strip()
        elif src == "base64":
            b64 = getattr(menu, "image_base64", None)
            if b64 and b64.strip():
                return f"data:image/jpeg;base64,{b64.strip()}"

    return getattr(menu, "image_url", None) or None


class MenuCreate(BaseModel):
    store_id: int
    name: str
    description: Optional[str] = None
    unit_price: float
    image_url: Optional[str] = None
    barcode: Optional[str] = None
    addon_options: Optional[str] = None  # JSON: [{"name":"ไข่ดาว","price":10},{"name":"พิเศษ","price":20}]
    is_active: bool = True


class MenuUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    unit_price: Optional[float] = None
    image_url: Optional[str] = None
    barcode: Optional[str] = None
    addon_options: Optional[str] = None
    is_active: Optional[bool] = None


class MenuResponse(BaseModel):
    id: int
    store_id: int
    name: str
    description: Optional[str] = None
    unit_price: float
    image_url: Optional[str] = None
    image_src: Optional[str] = None
    barcode: Optional[str] = None
    addon_options: Optional[str] = None  # JSON array of {name, price}
    is_active: bool
    created_at: str
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


def _menu_to_response(menu: Menu, base_url: str = None, locale: str = "th") -> dict:
    """แปลง Menu เป็น dict สำหรับ MenuResponse พร้อม image_src และ resolve ภาษาตาม locale"""
    name_i18n = getattr(menu, "name_i18n", None)
    desc_i18n = getattr(menu, "description_i18n", None)
    name = resolve_i18n(name_i18n, menu.name, locale)
    description = resolve_i18n(desc_i18n, menu.description, locale)
    addon_raw = getattr(menu, "addon_options", None)
    addon_options = resolve_addon_options(addon_raw, locale) if addon_raw else None
    return {
        "id": menu.id,
        "store_id": menu.store_id,
        "name": name or menu.name,
        "description": description or menu.description,
        "unit_price": menu.unit_price,
        "image_url": getattr(menu, "image_url", None),
        "image_src": _resolve_image_src(menu, base_url or BACKEND_URL or ""),
        "barcode": getattr(menu, "barcode", None),
        "addon_options": addon_options or addon_raw,
        "is_active": menu.is_active,
        "created_at": menu.created_at.isoformat() if menu.created_at else "",
        "updated_at": menu.updated_at.isoformat() if menu.updated_at else None,
    }


@router.post("/", response_model=MenuResponse)
async def create_menu(menu: MenuCreate, db: Session = Depends(get_db)):
    """
    สร้างรายการสินค้าใหม่
    """
    # ตรวจสอบว่า store มีอยู่จริง
    store = db.query(Store).filter(Store.id == menu.store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    
    new_menu = Menu(
        store_id=menu.store_id,
        name=menu.name,
        description=menu.description,
        unit_price=menu.unit_price,
        image_url=menu.image_url,
        barcode=menu.barcode,
        addon_options=menu.addon_options,
        is_active=menu.is_active
    )
    db.add(new_menu)
    db.commit()
    db.refresh(new_menu)
    return MenuResponse(**_menu_to_response(new_menu))


def _get_store_locale(db: Session, store_id: int) -> str:
    from app.models import StoreLocaleSetting
    row = db.query(StoreLocaleSetting).filter(StoreLocaleSetting.store_id == store_id).first()
    return row.locale if row else "th"


@router.get("/store/{store_id}", response_model=List[MenuResponse])
async def get_menus_by_store(
    store_id: int,
    is_active: Optional[bool] = None,
    locale: Optional[str] = Query(None, description="ภาษา (th,en,lo,...) - ไม่ระบุใช้ตามร้าน"),
    db: Session = Depends(get_db)
):
    """
    ดึงรายการสินค้าตาม store_id (name, description, addon ตาม locale)
    """
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    
    loc = locale or _get_store_locale(db, store_id)
    
    query = db.query(Menu).filter(Menu.store_id == store_id)
    if is_active is not None:
        query = query.filter(Menu.is_active == is_active)
    
    menus = query.order_by(Menu.created_at.desc()).all()
    base = (BACKEND_URL or "").rstrip("/")
    return [MenuResponse(**_menu_to_response(menu, base, loc)) for menu in menus]


@router.get("/{menu_id}", response_model=MenuResponse)
async def get_menu(
    menu_id: int,
    locale: Optional[str] = Query(None, description="ภาษา (th,en,...) - ไม่ระบุใช้ th"),
    store_id: Optional[int] = Query(None, description="store_id สำหรับดึง locale ของร้าน"),
    db: Session = Depends(get_db)
):
    """
    ดึงข้อมูลรายการสินค้า (name, description, addon ตาม locale)
    """
    menu = db.query(Menu).filter(Menu.id == menu_id).first()
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")
    loc = locale or (_get_store_locale(db, store_id) if store_id else "th")
    base = (BACKEND_URL or "").rstrip("/")
    return MenuResponse(**_menu_to_response(menu, base, loc))


@router.get("/store/{store_id}/by-barcode/{barcode_or_id}")
async def get_menu_by_barcode(
    store_id: int,
    barcode_or_id: str,
    locale: Optional[str] = Query(None, description="ภาษา"),
    db: Session = Depends(get_db)
):
    """
    ค้นหารายการสินค้าจากบาร์โค้ดหรือรหัส (id)
    """
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    loc = locale or _get_store_locale(db, store_id)
    barcode_clean = (barcode_or_id or "").strip()
    if not barcode_clean:
        raise HTTPException(status_code=400, detail="barcode or id required")
    base = (BACKEND_URL or "").rstrip("/")
    if barcode_clean.isdigit():
        menu = db.query(Menu).filter(Menu.store_id == store_id, Menu.id == int(barcode_clean)).first()
        if menu:
            return MenuResponse(**_menu_to_response(menu, base, loc))
    menu = db.query(Menu).filter(Menu.store_id == store_id, Menu.barcode == barcode_clean).first()
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found for barcode/id")
    return MenuResponse(**_menu_to_response(menu, base, loc))


def _get_session_user_id(request: Request) -> Optional[int]:
    """ดึง user_id จาก session ถ้ามี (สำหรับ Store POS / Admin)"""
    try:
        from app.api.auth import _get_session_user
        u = _get_session_user(request)
        return u.get("user_id") if u else None
    except Exception:
        return None


@router.put("/{menu_id}", response_model=MenuResponse)
async def update_menu(
    menu_id: int,
    menu_update: MenuUpdate,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    อัปเดตรายการสินค้า (เก็บราคาเดิมใน menu_price_logs เมื่อ unit_price/addon เปลี่ยน)
    """
    menu = db.query(Menu).filter(Menu.id == menu_id).first()
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")

    old_price = menu.unit_price
    old_addon = menu.addon_options
    price_changed = menu_update.unit_price is not None and menu_update.unit_price != old_price
    addon_changed = menu_update.addon_options is not None and menu_update.addon_options != old_addon

    if price_changed or addon_changed:
        pl = MenuPriceLog(
            menu_id=menu.id,
            unit_price=old_price,
            addon_options_json=old_addon,
            changed_by_user_id=_get_session_user_id(request),
        )
        db.add(pl)

    if menu_update.name is not None:
        menu.name = menu_update.name
    if menu_update.description is not None:
        menu.description = menu_update.description
    if menu_update.unit_price is not None:
        menu.unit_price = menu_update.unit_price
    if menu_update.image_url is not None:
        menu.image_url = menu_update.image_url
    if menu_update.barcode is not None:
        menu.barcode = menu_update.barcode
    if menu_update.addon_options is not None:
        menu.addon_options = menu_update.addon_options
    if menu_update.is_active is not None:
        menu.is_active = menu_update.is_active

    db.commit()
    db.refresh(menu)

    user_id = _get_session_user_id(request)
    ip = request.client.host if request.client else None
    write_audit_log(
        db, action="menu_update", table_name="menus", record_id=menu.id,
        old_values={"unit_price": old_price, "addon_options": old_addon} if (price_changed or addon_changed) else None,
        new_values={"unit_price": menu.unit_price, "addon_options": menu.addon_options},
        user_id=user_id, source="store_pos" if user_id else "system", ip_address=ip,
    )
    return MenuResponse(**_menu_to_response(menu))


class FetchImageRequest(BaseModel):
    url: str


@router.post("/fetch-image-base64")
async def fetch_image_base64(req: FetchImageRequest):
    """
    ดาวน์โหลดรูปจาก URL → resize เล็ก → คืน base64 (สำหรับ addon รูป)
    """
    b64, err = fetch_url_to_base64(req.url.strip())
    if err:
        raise HTTPException(status_code=400, detail=err)
    return {"base64": b64}


@router.post("/{menu_id}/download-image")
async def download_menu_image(
    menu_id: int,
    image_url: Optional[str] = Query(None, description="URL รูปจาก Internet (ถ้าไม่ระบุใช้จาก menu.image_url)"),
    db: Session = Depends(get_db)
):
    """
    ดาวน์โหลดรูปจาก URL → resize 480x640 → บันทึก local + base64 ใน DB
    """
    menu = db.query(Menu).filter(Menu.id == menu_id).first()
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")
    url = (image_url or "").strip() or getattr(menu, "image_url", None) or ""
    if not url:
        raise HTTPException(status_code=400, detail="ระบุ image_url หรือตั้งค่า menu.image_url ก่อน")

    try:
        local_path, b64, err = download_and_save(url, menu.store_id, menu.id)
        if err and not local_path:
            raise HTTPException(status_code=502, detail=f"Download failed: {err}")

        menu.image_local = local_path
        menu.image_base64 = b64
        if not menu.image_url:
            menu.image_url = url
        db.commit()
        db.refresh(menu)
        return {"ok": True, "image_local": local_path, "message": "Image downloaded and saved"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Save failed: {str(e)}")


@router.delete("/{menu_id}")
async def delete_menu(menu_id: int, db: Session = Depends(get_db)):
    """
    ลบรายการสินค้า
    """
    menu = db.query(Menu).filter(Menu.id == menu_id).first()
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")
    
    db.delete(menu)
    db.commit()
    
    return {"message": "Menu deleted successfully"}

