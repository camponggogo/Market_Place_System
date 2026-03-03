"""
Locale & Currency Settings API – ตั้งค่าภาษาและหน่วยเงิน (ต่อร้าน store_id)
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Locale, Currency, AppSetting, ProgramSetting, StoreLocaleSetting, Store

router = APIRouter(prefix="/api/locale-settings", tags=["locale-settings"])

VALID_LOCALES = {"th", "en", "lo", "my", "kh", "ms", "shn", "zh", "ru"}
CURRENCY_MAP = {
    "th": ("THB", "฿", "Baht"),
    "en": ("USD", "$", "Dollar"),
    "lo": ("LAK", "₭", "Kip"),
    "my": ("MMK", "K", "Kyat"),
    "kh": ("KHR", "៛", "Riel"),
    "ms": ("MYR", "RM", "Ringgit"),
    "shn": ("MMK", "K", "Kyat"),
    "zh": ("CNY", "¥", "Yuan"),
    "ru": ("RUB", "₽", "Ruble"),
}


def _get_global_setting(db: Session, key: str) -> Optional[str]:
    row = db.query(AppSetting).filter(AppSetting.key == key).first()
    return row.value if row else None


def _get_store_locale(db: Session, store_id: int) -> Optional[StoreLocaleSetting]:
    return db.query(StoreLocaleSetting).filter(StoreLocaleSetting.store_id == store_id).first()


def _resolve_locale(db: Session, store_id: Optional[int]) -> tuple:
    """คืน (locale, currency_code, currency_symbol, currency_name)"""
    if store_id:
        row = _get_store_locale(db, store_id)
        if row:
            return (row.locale, row.currency_code, row.currency_symbol, row.currency_name or "Baht")
    return (
        _get_global_setting(db, "locale") or "th",
        _get_global_setting(db, "currency_code") or "THB",
        _get_global_setting(db, "currency_symbol") or "฿",
        _get_global_setting(db, "currency_name") or "Baht",
    )


class LocaleSettingsResponse(BaseModel):
    locale: str
    currency_code: str
    currency_symbol: str
    currency_name: str
    translations: dict


class LocaleUpdateBody(BaseModel):
    locale: Optional[str] = None
    currency_code: Optional[str] = None
    store_id: Optional[int] = None


@router.get("/locales", response_model=List[dict])
def list_locales(db: Session = Depends(get_db)):
    """รายการภาษาที่รองรับ"""
    rows = db.query(Locale).order_by(Locale.id).all()
    return [{"code": r.code, "name": r.name} for r in rows]


@router.get("/currencies", response_model=List[dict])
def list_currencies(db: Session = Depends(get_db)):
    """รายการหน่วยเงินที่รองรับ"""
    rows = db.query(Currency).order_by(Currency.id).all()
    return [{"code": r.code, "symbol": r.symbol, "name": r.name} for r in rows]


@router.get("", response_model=LocaleSettingsResponse)
def get_locale_settings(
    store_id: Optional[int] = Query(None, description="ร้านที่ต้องการ - ถ้าไม่ระบุใช้ค่าทั่วไป"),
    locale: Optional[str] = Query(None, description="Override ภาษา (th,en,lo,...) - สำหรับ admin/customer"),
    db: Session = Depends(get_db),
):
    """ดึงการตั้งค่าภาษา หน่วยเงิน และคำแปล (ตาม store_id ถ้ามี) - labels จาก program_settings"""
    base_locale, currency_code, currency_symbol, currency_name = _resolve_locale(db, store_id)
    locale = locale if locale and locale in VALID_LOCALES else base_locale

    # อ่าน labels จาก program_settings (แต่ละ row = label key, แต่ละ column = ภาษา)
    col_map = {"th": "label_th", "en": "label_en", "lo": "label_lo", "my": "label_my",
               "kh": "label_kh", "ms": "label_ms", "shn": "label_shn", "zh": "label_zh", "ru": "label_ru"}
    fallback_order = [locale, "en", "th"] if locale != "th" else [locale, "en"]
    translations = {}
    try:
        rows = db.query(ProgramSetting).all()
        for r in rows:
            val = None
            for loc in fallback_order:
                col = col_map.get(loc)
                if col:
                    val = getattr(r, col, None)
                    if val:
                        break
            if val:
                translations[r.label_key] = val
    except Exception:
        pass  # ตาราง program_settings อาจยังไม่มี

    return LocaleSettingsResponse(
        locale=locale,
        currency_code=currency_code,
        currency_symbol=currency_symbol,
        currency_name=currency_name,
        translations=translations,
    )


@router.put("")
def update_locale_settings(body: LocaleUpdateBody, db: Session = Depends(get_db)):
    """อัปเดตการตั้งค่าภาษาและหน่วยเงิน (ต่อร้าน store_id)"""
    store_id = body.store_id or 1
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")

    row = _get_store_locale(db, store_id)
    if not row:
        row = StoreLocaleSetting(
            store_id=store_id,
            locale=_get_global_setting(db, "locale") or "th",
            currency_code=_get_global_setting(db, "currency_code") or "THB",
            currency_symbol=_get_global_setting(db, "currency_symbol") or "฿",
            currency_name=_get_global_setting(db, "currency_name") or "Baht",
        )
        db.add(row)
        db.flush()

    if body.locale is not None:
        if body.locale not in VALID_LOCALES:
            raise HTTPException(status_code=400, detail=f"Invalid locale. Valid: {VALID_LOCALES}")
        row.locale = body.locale
        if body.currency_code is None and body.locale in CURRENCY_MAP:
            code, symbol, name = CURRENCY_MAP[body.locale]
            row.currency_code = code
            row.currency_symbol = symbol
            row.currency_name = name

    if body.currency_code is not None:
        curr = db.query(Currency).filter(Currency.code == body.currency_code).first()
        if not curr:
            raise HTTPException(status_code=400, detail="Currency not found")
        row.currency_code = curr.code
        row.currency_symbol = curr.symbol
        row.currency_name = curr.name

    db.commit()
    db.refresh(row)
    return get_locale_settings(store_id=store_id, db=db)
