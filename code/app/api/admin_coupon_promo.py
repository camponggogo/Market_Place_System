# Admin Coupon Promo API - ตั้งค่าคูปองโปรโมชั่น (เงื่อนไขเติมเงินได้คูปอง, ร้านที่ร่วม, วันเวลาใช้ได้)
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import CouponPromo, Store
from app.api.auth import require_admin

router = APIRouter(prefix="/api/admin/coupon-promo", tags=["admin-coupon-promo"])


class CouponPromoCreate(BaseModel):
    title: str
    description: Optional[str] = None
    min_topup_amount: float
    discount_amount: float
    valid_from: Optional[str] = None  # ISO datetime
    valid_to: Optional[str] = None
    store_ids: Optional[List[int]] = None  # ว่าง = ทุกร้าน
    is_active: bool = True


class CouponPromoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    min_topup_amount: Optional[float] = None
    discount_amount: Optional[float] = None
    valid_from: Optional[str] = None
    valid_to: Optional[str] = None
    store_ids: Optional[List[int]] = None
    is_active: Optional[bool] = None


def _parse_store_ids_json(s: Optional[str]) -> List[int]:
    if not s or not s.strip():
        return []
    try:
        import json
        out = json.loads(s)
        return [int(x) for x in out] if isinstance(out, list) else []
    except Exception:
        return []


def _store_ids_to_json(ids: Optional[List[int]]) -> Optional[str]:
    if not ids:
        return None
    import json
    return json.dumps(ids)


@router.get("/list")
def list_coupon_promos(db: Session = Depends(get_db), _admin=Depends(require_admin)):
    rows = db.query(CouponPromo).order_by(CouponPromo.id.desc()).all()
    return [
        {
            "id": r.id,
            "title": r.title,
            "description": r.description,
            "min_topup_amount": float(r.min_topup_amount),
            "discount_amount": float(r.discount_amount),
            "valid_from": r.valid_from.isoformat() if r.valid_from else None,
            "valid_to": r.valid_to.isoformat() if r.valid_to else None,
            "store_ids": _parse_store_ids_json(r.store_ids),
            "is_active": r.is_active,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


@router.get("/stores")
def list_stores_for_promo(db: Session = Depends(get_db), _admin=Depends(require_admin)):
    """รายการร้านสำหรับเลือกร่วมรายการคูปอง"""
    rows = db.query(Store).order_by(Store.id).all()
    return [{"id": s.id, "name": getattr(s, "name", None) or f"Store {s.id}"} for s in rows]


@router.post("/create")
def create_coupon_promo(body: CouponPromoCreate, db: Session = Depends(get_db), _admin=Depends(require_admin)):
    if body.min_topup_amount < 0 or body.discount_amount <= 0:
        raise HTTPException(status_code=400, detail="min_topup_amount ต้องไม่ติดลบ และ discount_amount ต้องมากกว่า 0")
    valid_from = None
    valid_to = None
    if body.valid_from:
        try:
            valid_from = datetime.fromisoformat(body.valid_from.replace("Z", "+00:00"))
        except Exception:
            pass
    if body.valid_to:
        try:
            valid_to = datetime.fromisoformat(body.valid_to.replace("Z", "+00:00"))
        except Exception:
            pass
    promo = CouponPromo(
        title=body.title,
        description=body.description,
        min_topup_amount=body.min_topup_amount,
        discount_amount=body.discount_amount,
        valid_from=valid_from,
        valid_to=valid_to,
        store_ids=_store_ids_to_json(body.store_ids),
        is_active=body.is_active,
    )
    db.add(promo)
    db.commit()
    db.refresh(promo)
    return {
        "id": promo.id,
        "title": promo.title,
        "min_topup_amount": float(promo.min_topup_amount),
        "discount_amount": float(promo.discount_amount),
        "valid_from": promo.valid_from.isoformat() if promo.valid_from else None,
        "valid_to": promo.valid_to.isoformat() if promo.valid_to else None,
        "store_ids": _parse_store_ids_json(promo.store_ids),
        "is_active": promo.is_active,
    }


@router.put("/{promo_id}")
def update_coupon_promo(
    promo_id: int,
    body: CouponPromoUpdate,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    promo = db.query(CouponPromo).filter(CouponPromo.id == promo_id).first()
    if not promo:
        raise HTTPException(status_code=404, detail="ไม่พบโปรโมชั่นคูปอง")
    if body.title is not None:
        promo.title = body.title
    if body.description is not None:
        promo.description = body.description
    if body.min_topup_amount is not None:
        if body.min_topup_amount < 0:
            raise HTTPException(status_code=400, detail="min_topup_amount ต้องไม่ติดลบ")
        promo.min_topup_amount = body.min_topup_amount
    if body.discount_amount is not None:
        if body.discount_amount <= 0:
            raise HTTPException(status_code=400, detail="discount_amount ต้องมากกว่า 0")
        promo.discount_amount = body.discount_amount
    if body.valid_from is not None:
        try:
            promo.valid_from = datetime.fromisoformat(body.valid_from.replace("Z", "+00:00")) if body.valid_from else None
        except Exception:
            pass
    if body.valid_to is not None:
        try:
            promo.valid_to = datetime.fromisoformat(body.valid_to.replace("Z", "+00:00")) if body.valid_to else None
        except Exception:
            pass
    if body.store_ids is not None:
        promo.store_ids = _store_ids_to_json(body.store_ids)
    if body.is_active is not None:
        promo.is_active = body.is_active
    db.add(promo)
    db.commit()
    db.refresh(promo)
    return {
        "id": promo.id,
        "title": promo.title,
        "min_topup_amount": float(promo.min_topup_amount),
        "discount_amount": float(promo.discount_amount),
        "valid_from": promo.valid_from.isoformat() if promo.valid_from else None,
        "valid_to": promo.valid_to.isoformat() if promo.valid_to else None,
        "store_ids": _parse_store_ids_json(promo.store_ids),
        "is_active": promo.is_active,
    }


@router.delete("/{promo_id}")
def delete_coupon_promo(promo_id: int, db: Session = Depends(get_db), _admin=Depends(require_admin)):
    promo = db.query(CouponPromo).filter(CouponPromo.id == promo_id).first()
    if not promo:
        raise HTTPException(status_code=404, detail="ไม่พบโปรโมชั่นคูปอง")
    db.delete(promo)
    db.commit()
    return {"success": True}
