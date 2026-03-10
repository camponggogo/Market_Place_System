"""
Member Scan-Pay API - อ่าน QR PromptPay (plain text) ดึง store_id, order_id แล้วหักจ่ายด้วย e-coupon
กรองคูปองตาม valid_from/valid_to และร้านที่ร่วมรายการ; รองรับ use_coupon (ไม่ใช้คูปองจากหน้า member)
"""
import re
import json
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models import Customer, ECoupon, Order, MemberActivity
from app.api.member import get_current_customer

router = APIRouter(prefix="/api/member", tags=["member"])


def _parse_allowed_store_ids(s: Optional[str]) -> List[int]:
    if not s or not s.strip():
        return []
    try:
        out = json.loads(s)
        return [int(x) for x in out] if isinstance(out, list) else []
    except Exception:
        return []


def _coupon_valid_for_store(ec: ECoupon, store_id: int) -> bool:
    allowed = _parse_allowed_store_ids(ec.allowed_store_ids)
    if not allowed:
        return True
    return store_id in allowed


def parse_promptpay_qr(qr_text: str) -> dict:
    """
    อ่านข้อความจาก QR PromptPay (plain text) แล้วดึง store_id, order_id
    รูปแบบที่รองรับ: ref1=store_token, ref2=order_id หรือ query string ที่มี store_id, order_id
    """
    out = {"store_id": None, "order_id": None, "amount": None}
    if not qr_text or not qr_text.strip():
        return out
    text = qr_text.strip()
    # ลองแบบ ref1=xxx&ref2=yyy หรือ store_id=1&order_id=2
    for part in re.split(r"[&?\s]+", text):
        if "=" in part:
            k, v = part.split("=", 1)
            k, v = k.strip().lower(), v.strip()
            if k in ("store_id", "ref1"):  # ref1 อาจเป็น store token
                try:
                    out["store_id"] = int(v) if v.isdigit() else None
                except ValueError:
                    pass
            elif k in ("order_id", "ref2"):
                try:
                    out["order_id"] = int(v) if v.isdigit() else None
                except ValueError:
                    pass
            elif k == "amount":
                try:
                    out["amount"] = float(v)
                except ValueError:
                    pass
    # ถ้า ref1 เป็นตัวเลข 20 หลัก (store token) อาจต้อง map กับ store_id จาก DB
    return out


class ScanPayRequest(BaseModel):
    qr_text: Optional[str] = None  # ข้อความจาก QR ที่สแกนได้
    store_id: Optional[int] = None  # ถ้าส่งตรงมา
    order_id: Optional[int] = None
    amount: Optional[float] = None
    use_coupon: Optional[bool] = None  # True=ใช้คูปอง, False=ไม่ใช้ (เลือกจากหน้า member), ไม่ส่ง=ใช้ตาม auto_apply_coupon


class ScanPayResponse(BaseModel):
    success: bool
    message: str
    order_id: Optional[int] = None
    amount_deducted: Optional[float] = None


@router.post("/scan-pay", response_model=ScanPayResponse)
def scan_pay(
    data: ScanPayRequest,
    customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db),
):
    store_id = data.store_id
    order_id = data.order_id
    amount = data.amount

    if data.qr_text:
        parsed = parse_promptpay_qr(data.qr_text)
        if parsed.get("store_id") is not None:
            store_id = parsed["store_id"]
        if parsed.get("order_id") is not None:
            order_id = parsed["order_id"]
        if parsed.get("amount") is not None and amount is None:
            amount = parsed["amount"]

    if not order_id and not amount:
        raise HTTPException(status_code=400, detail="ไม่พบ order_id หรือ amount จาก QR หรือคำขอ")

    order = None
    if order_id:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="ไม่พบรายการสั่งซื้อ")
        if store_id and order.store_id != store_id:
            raise HTTPException(status_code=400, detail="ร้านไม่ตรงกับรายการสั่งซื้อ")
        store_id = order.store_id
        amount = float(order.total_amount) if amount is None else amount
    else:
        if not store_id or amount is None or amount <= 0:
            raise HTTPException(status_code=400, detail="ต้องระบุ store_id และ amount")

    # ถ้าสมาชิกเลือกไม่ใช้คูปอง (use_coupon=False) หรือส่ง True แต่ระบบปิด auto_apply ก็ยังใช้ได้ถ้าส่ง True
    use_coupon = data.use_coupon if data.use_coupon is not None else getattr(customer, "auto_apply_coupon", True)
    if not use_coupon:
        raise HTTPException(
            status_code=400,
            detail="คุณเลือกไม่ใช้คูปองสำหรับการชำระนี้ กรุณาชำระด้วยวิธีอื่นหรือเปลี่ยนการตั้งค่าในหน้า Member",
        )

    now_utc = datetime.utcnow()
    # หา e-coupon ที่ assigned ให้ลูกค้า อยู่ในช่วงใช้ได้ (valid_from/valid_to) และใช้ได้ที่ร้านนี้
    all_assigned = (
        db.query(ECoupon)
        .filter(ECoupon.customer_id == customer.id, ECoupon.status == "assigned")
        .order_by(ECoupon.id.asc())
        .all()
    )
    available = []
    for ec in all_assigned:
        if ec.valid_from and ec.valid_from > now_utc:
            continue
        if ec.valid_to and ec.valid_to < now_utc:
            continue
        if not _coupon_valid_for_store(ec, store_id):
            continue
        available.append(ec)
    total_available = sum(float(c.amount) for c in available)
    if total_available < amount:
        raise HTTPException(
            status_code=400,
            detail=f"ยอด e-coupon ไม่พอ (มี {total_available:.2f} บาท ต้องการ {amount:.2f} บาท)",
        )

    remaining = amount
    for ec in available:
        if remaining <= 0:
            break
        use = min(remaining, float(ec.amount))
        ec.store_id = store_id
        ec.order_id = order.id if order else None
        ec.redeemed_at = datetime.utcnow()
        if use >= float(ec.amount):
            ec.status = "used"
            ec.amount = 0
        else:
            ec.amount = float(ec.amount) - use
        remaining -= use
        db.add(ec)

    act = MemberActivity(
        customer_id=customer.id,
        activity_type="payment",
        amount=amount,
        description=f"จ่ายด้วย e-coupon ที่ร้าน store_id={store_id}" + (f" order_id={order_id}" if order_id else ""),
        ref_id=order_id,
    )
    db.add(act)
    if order:
        order.status = "paid"
        order.paid_at = datetime.utcnow()
        db.add(order)
    db.commit()

    return ScanPayResponse(
        success=True,
        message="หักจ่ายด้วย e-coupon เรียบร้อย",
        order_id=order_id,
        amount_deducted=amount,
    )
