# Admin E-Coupon API - ออก/แลก E-Coupon
from typing import Optional
from datetime import datetime
import secrets
import string
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.database import get_db
from app.models import ECoupon, Customer
from sqlalchemy.orm import Session
from fastapi import Depends

router = APIRouter(prefix="/api/admin/ecoupon", tags=["admin-ecoupon"])
PAYMENT_METHODS = ["cash", "promptpay", "credit_debit", "omise", "stripe", "alipay", "wechat_pay", "line_pay", "true_wallet", "e_money"]

def _gen_code(prefix="EC", length=10):
    return prefix + "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(length))

class IssueECouponRequest(BaseModel):
    amount: float
    payment_method: str
    customer_id: Optional[int] = None
    paid_at: Optional[str] = None

@router.post("/issue")
def issue_ecoupon(data: IssueECouponRequest, db: Session = Depends(get_db)):
    if data.amount <= 0:
        raise HTTPException(status_code=400, detail="จำนวนต้องมากกว่า 0")
    if data.payment_method not in PAYMENT_METHODS:
        raise HTTPException(status_code=400, detail="วิธีชำระไม่รองรับ")
    code = _gen_code()
    while db.query(ECoupon).filter(ECoupon.code == code).first():
        code = _gen_code()
    paid_at = datetime.utcnow()
    if data.paid_at:
        try:
            paid_at = datetime.fromisoformat(data.paid_at.replace("Z", "+00:00"))
        except Exception:
            pass
    status = "assigned" if data.customer_id else "available"
    if data.customer_id and not db.query(Customer).filter(Customer.id == data.customer_id).first():
        raise HTTPException(status_code=404, detail="ไม่พบลูกค้า")
    ec = ECoupon(code=code, amount=data.amount, customer_id=data.customer_id, status=status, payment_method=data.payment_method, paid_at=paid_at)
    db.add(ec)
    db.commit()
    db.refresh(ec)
    return {"success": True, "code": ec.code, "amount": float(ec.amount), "status": ec.status, "customer_id": ec.customer_id}

@router.get("/list")
def list_ecoupons(status: Optional[str] = None, customer_id: Optional[int] = None, limit: int = 100, db: Session = Depends(get_db)):
    q = db.query(ECoupon)
    if status:
        q = q.filter(ECoupon.status == status)
    if customer_id is not None:
        q = q.filter(ECoupon.customer_id == customer_id)
    rows = q.order_by(ECoupon.id.desc()).limit(limit).all()
    return [{"id": r.id, "code": r.code, "amount": float(r.amount), "customer_id": r.customer_id, "status": r.status, "payment_method": r.payment_method, "paid_at": r.paid_at.isoformat() if r.paid_at else None, "redeemed_at": r.redeemed_at.isoformat() if r.redeemed_at else None, "order_id": r.order_id, "created_at": r.created_at.isoformat() if r.created_at else None} for r in rows]

class AssignRequest(BaseModel):
    code: str
    customer_id: int

@router.post("/assign")
def assign_ecoupon(data: AssignRequest, db: Session = Depends(get_db)):
    ec = db.query(ECoupon).filter(ECoupon.code == data.code.strip()).first()
    if not ec:
        raise HTTPException(status_code=404, detail="ไม่พบ e-coupon")
    if ec.status != "available":
        raise HTTPException(status_code=400, detail="e-coupon ถูกใช้หรือกำหนดแล้ว")
    if not db.query(Customer).filter(Customer.id == data.customer_id).first():
        raise HTTPException(status_code=404, detail="ไม่พบลูกค้า")
    ec.customer_id = data.customer_id
    ec.status = "assigned"
    db.add(ec)
    db.commit()
    return {"success": True, "message": "กำหนดให้ลูกค้าเรียบร้อย"}
