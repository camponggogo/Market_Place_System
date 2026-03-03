"""
Program Settings API – จัดการ labels หลายภาษา (program_settings)
แต่ละ row = label key, แต่ละ column = ภาษา
"""
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ProgramSetting

router = APIRouter(prefix="/api/program-settings", tags=["program-settings"])

LOCALE_COLS = ["label_th", "label_en", "label_lo", "label_my", "label_kh", "label_ms", "label_shn", "label_zh", "label_ru"]


class ProgramSettingUpdate(BaseModel):
    """อัปเดต labels ตามภาษา (ส่งเฉพาะภาษาที่ต้องการแก้)"""
    label_key: str
    label_th: Optional[str] = None
    label_en: Optional[str] = None
    label_lo: Optional[str] = None
    label_my: Optional[str] = None
    label_kh: Optional[str] = None
    label_ms: Optional[str] = None
    label_shn: Optional[str] = None
    label_zh: Optional[str] = None
    label_ru: Optional[str] = None


@router.get("")
def list_program_settings(db: Session = Depends(get_db)):
    """
    ดึง labels ทั้งหมด (แต่ละ row = label_key พร้อมค่าทุกภาษา)
    """
    rows = db.query(ProgramSetting).order_by(ProgramSetting.label_key).all()
    return [
        {
            "label_key": r.label_key,
            "label_th": r.label_th,
            "label_en": r.label_en,
            "label_lo": r.label_lo,
            "label_my": r.label_my,
            "label_kh": r.label_kh,
            "label_ms": r.label_ms,
            "label_shn": r.label_shn,
            "label_zh": r.label_zh,
            "label_ru": r.label_ru,
        }
        for r in rows
    ]


@router.put("/{label_key}")
def update_program_setting(label_key: str, body: ProgramSettingUpdate, db: Session = Depends(get_db)):
    """
    อัปเดต label ตาม label_key
    """
    row = db.query(ProgramSetting).filter(ProgramSetting.label_key == label_key).first()
    if not row:
        raise HTTPException(status_code=404, detail=f"Label key '{label_key}' not found")

    for col in LOCALE_COLS:
        val = getattr(body, col, None)
        if val is not None:
            setattr(row, col, val)

    db.commit()
    db.refresh(row)
    return {"label_key": row.label_key, "ok": True}


@router.post("")
def create_program_setting(body: ProgramSettingUpdate, db: Session = Depends(get_db)):
    """
    สร้าง label ใหม่
    """
    if db.query(ProgramSetting).filter(ProgramSetting.label_key == body.label_key).first():
        raise HTTPException(status_code=400, detail=f"Label key '{body.label_key}' already exists")

    row = ProgramSetting(label_key=body.label_key)
    for col in LOCALE_COLS:
        attr = col  # body has label_th, label_en, etc.
        val = getattr(body, col, None)
        if val is not None:
            setattr(row, col, val)

    db.add(row)
    db.commit()
    db.refresh(row)
    return {"label_key": row.label_key, "ok": True}
