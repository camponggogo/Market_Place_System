"""
Member API - ลูกค้าสมาชิกออนไลน์: ลงทะเบียน, ล็อกอิน, ข้อมูลส่วนตัว, ยอดเงิน, แต้ม, คูปอง, โปรโมชั่น
"""
import re
from datetime import datetime, timedelta
from typing import List, Optional, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    Customer,
    CustomerBalance,
    MemberPointsLedger,
    MemberVoucher,
    VoucherDefinition,
    StorePromotion,
    ECoupon,
    AdFeed,
    AdImpression,
    MemberActivity,
    Store,
)
from app.config import SECRET_KEY, STRIPE_SECRET_KEY, STRIPE_PUBLISHABLE_KEY, BACKEND_URL
from app.services import stripe_promptpay

router = APIRouter(prefix="/api/member", tags=["member"])
security = HTTPBearer(auto_error=False)

# JWT
ALGORITHM = "HS256"
ACCESS_EXPIRE = 60 * 60 * 24 * 30  # 30 วัน


def _hash_password(pwd: str) -> str:
    try:
        import bcrypt
        return bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()
    except ImportError:
        from passlib.context import CryptContext
        return CryptContext(schemes=["bcrypt"], deprecated="auto").hash(pwd)


def _verify_password(plain: str, hashed: str) -> bool:
    try:
        import bcrypt
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except ImportError:
        from passlib.context import CryptContext
        return CryptContext(schemes=["bcrypt"], deprecated="auto").verify(plain, hashed)


def create_token(customer_id: int) -> str:
    return jwt.encode(
        {"sub": str(customer_id), "exp": datetime.utcnow() + timedelta(seconds=ACCESS_EXPIRE)},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def get_current_customer(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> Customer:
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="กรุณาเข้าสู่ระบบ")
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        customer_id = int(payload.get("sub"))
    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail="โทเค็นไม่ถูกต้อง")
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=401, detail="ไม่พบสมาชิก")
    return customer


def get_current_customer_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> Optional[Customer]:
    """คืน Customer ถ้ามี token ถูกต้อง ไม่งั้นคืน None"""
    if not credentials or not credentials.credentials:
        return None
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        customer_id = int(payload.get("sub"))
    except (JWTError, ValueError):
        return None
    return db.query(Customer).filter(Customer.id == customer_id).first()


# --- Register ---
class RegisterRequest(BaseModel):
    username: str  # 4 ตัวขึ้นไป
    phone: str
    password: str
    email: Optional[str] = None
    name: Optional[str] = None


class RegisterResponse(BaseModel):
    success: bool
    customer_id: int
    message: str


@router.post("/register", response_model=RegisterResponse)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    if len(data.username.strip()) < 4:
        raise HTTPException(status_code=400, detail="ชื่อผู้ใช้ต้องไม่น้อยกว่า 4 ตัวอักษร")
    if not re.match(r"^[a-zA-Z0-9_.-]+$", data.username):
        raise HTTPException(status_code=400, detail="ชื่อผู้ใช้ใช้ได้เฉพาะตัวอักษร ตัวเลข และ _ . -")
    if db.query(Customer).filter(Customer.username == data.username).first():
        raise HTTPException(status_code=400, detail="ชื่อผู้ใช้นี้ถูกใช้แล้ว")
    if db.query(Customer).filter(Customer.phone == data.phone).first():
        raise HTTPException(status_code=400, detail="หมายเลขโทรศัพท์นี้ถูกใช้แล้ว")
    if data.email and db.query(Customer).filter(Customer.email == data.email).first():
        raise HTTPException(status_code=400, detail="อีเมลนี้ถูกใช้แล้ว")

    customer = Customer(
        username=data.username.strip(),
        phone=data.phone.strip(),
        email=data.email.strip() if data.email else None,
        name=data.name.strip() if data.name else None,
        password_hash=_hash_password(data.password),
        total_points=0.0,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    balance = CustomerBalance(customer_id=customer.id, balance=0.0)
    db.add(balance)
    db.commit()
    return RegisterResponse(success=True, customer_id=customer.id, message="ลงทะเบียนสำเร็จ")


# --- Login ---
class LoginRequest(BaseModel):
    login_id: str  # username หรือ เบอร์โทร หรือ e-mail
    password: str


class LoginResponse(BaseModel):
    success: bool
    token: str
    customer_id: int
    username: Optional[str]
    name: Optional[str]
    phone: str


@router.post("/login", response_model=LoginResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    login_id = data.login_id.strip()
    customer = (
        db.query(Customer)
        .filter(
            (Customer.username == login_id) | (Customer.phone == login_id) | (Customer.email == login_id)
        )
        .first()
    )
    if not customer or not customer.password_hash:
        raise HTTPException(status_code=401, detail="ชื่อผู้ใช้ หรือรหัสผ่านไม่ถูกต้อง")
    if not _verify_password(data.password, customer.password_hash):
        raise HTTPException(status_code=401, detail="ชื่อผู้ใช้ หรือรหัสผ่านไม่ถูกต้อง")
    token = create_token(customer.id)
    return LoginResponse(
        success=True,
        token=token,
        customer_id=customer.id,
        username=customer.username,
        name=customer.name,
        phone=customer.phone,
    )


# --- Me / Dashboard ---
class DashboardResponse(BaseModel):
    customer_id: int
    username: Optional[str]
    name: Optional[str]
    phone: str
    email: Optional[str]
    balance: float
    total_points: float
    vouchers: List[dict]
    promotions: List[dict]
    e_coupon_balance: float  # ยอด e-coupon ที่ใช้จ่ายได้
    recent_activities: List[dict]


@router.get("/me", response_model=DashboardResponse)
def me(customer: Customer = Depends(get_current_customer), db: Session = Depends(get_db)):
    bal = db.query(CustomerBalance).filter(CustomerBalance.customer_id == customer.id).first()
    balance = float(bal.balance) if bal else 0.0
    vouchers = []
    for mv in db.query(MemberVoucher).join(VoucherDefinition).filter(
        MemberVoucher.customer_id == customer.id,
        MemberVoucher.used_at.is_(None),
        VoucherDefinition.is_active == True,
    ).all():
        vouchers.append({
            "id": mv.id,
            "name": mv.voucher_definition.name,
            "value": mv.voucher_definition.value,
            "valid_to": mv.voucher_definition.valid_to.isoformat() if mv.voucher_definition.valid_to else None,
        })
    promotions = []
    for p in db.query(StorePromotion).filter(StorePromotion.is_active == True).limit(20).all():
        promotions.append({
            "id": p.id,
            "store_id": p.store_id,
            "title": p.title,
            "description": p.description,
            "valid_to": p.valid_to.isoformat() if p.valid_to else None,
        })
    e_coupon_sum = db.query(ECoupon).filter(
        ECoupon.customer_id == customer.id,
        ECoupon.status == "assigned",
    ).all()
    e_coupon_balance = sum(float(c.amount) for c in e_coupon_sum)
    activities = db.query(MemberActivity).filter(MemberActivity.customer_id == customer.id).order_by(MemberActivity.id.desc()).limit(20).all()
    recent_activities = [
        {"id": a.id, "type": a.activity_type, "amount": a.amount, "description": a.description, "created_at": a.created_at.isoformat() if a.created_at else None}
        for a in activities
    ]
    return DashboardResponse(
        customer_id=customer.id,
        username=customer.username,
        name=customer.name,
        phone=customer.phone,
        email=customer.email,
        balance=balance,
        total_points=float(customer.total_points or 0),
        vouchers=vouchers,
        promotions=promotions,
        e_coupon_balance=e_coupon_balance,
        recent_activities=recent_activities,
    )


# --- Ad Feed (สำหรับหน้าแอปสมาชิก) - กรองตามช่วงเวลา start_at/end_at; store_id=null = ทุกร้าน ---
@router.get("/ads")
def list_ads(store_id: Optional[int] = Query(None, description="กรองโฆษณาตามร้าน; ไม่ส่ง = เฉพาะโฆษณาทุกร้าน"),
             db: Session = Depends(get_db)):
    from datetime import datetime
    from sqlalchemy import or_
    now = datetime.utcnow()
    q = db.query(AdFeed).filter(AdFeed.is_active == True)
    q = q.filter(or_(AdFeed.start_at == None, AdFeed.start_at <= now))
    q = q.filter(or_(AdFeed.end_at == None, AdFeed.end_at >= now))
    if store_id is not None:
        q = q.filter(or_(AdFeed.store_id == None, AdFeed.store_id == store_id))
    else:
        q = q.filter(AdFeed.store_id == None)
    rows = q.order_by(AdFeed.sort_order, AdFeed.id.desc()).all()
    return [{"id": r.id, "title": r.title, "body": r.body, "image_url": r.image_url, "link_url": r.link_url} for r in rows]


class AdTrackRequest(BaseModel):
    ad_feed_id: int
    event_type: Literal["view", "click"] = "view"


@router.post("/ads/track")
def track_ad(
    body: AdTrackRequest,
    db: Session = Depends(get_db),
    customer: Optional[Customer] = Depends(get_current_customer_optional),
):
    """บันทึกการดู/กดโฆษณา (สำหรับสรุปผล); สมาชิกล็อกอินส่ง token ได้ customer_id จะถูกเก็บ"""
    ad = db.query(AdFeed).filter(AdFeed.id == body.ad_feed_id).first()
    if not ad:
        raise HTTPException(status_code=404, detail="ไม่พบโฆษณา")
    customer_id = customer.id if customer else None
    imp = AdImpression(ad_feed_id=body.ad_feed_id, event_type=body.event_type, customer_id=customer_id)
    db.add(imp)
    db.commit()
    return {"ok": True}


# --- Stripe: เติมเงิน / ซื้อ E-Coupon (สำหรับทดสอบผ่าน Stripe) ---
@router.get("/stripe-config")
def member_stripe_config(customer: Customer = Depends(get_current_customer)):
    """คืนค่า Stripe Publishable Key สำหรับโหลด Stripe.js (ถ้าไม่ได้ตั้งค่า จะคืนค่าว่าง)"""
    return {"publishableKey": STRIPE_PUBLISHABLE_KEY or ""}


class StripeCreateIntentRequest(BaseModel):
    amount: float  # บาท
    intent_type: Literal["topup", "ecoupon"] = "topup"
    payment_method: Literal["card", "promptpay", "truewallet"] = "card"  # วิธีชำระ: บัตร / PromptPay / e-Wallet (TrueWallet)


@router.post("/stripe/create-payment-intent")
def member_stripe_create_payment_intent(
    body: StripeCreateIntentRequest,
    customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db),
):
    """
    สร้าง Stripe PaymentIntent สำหรับสมาชิก: เติมเงิน (topup) หรือซื้อ E-Coupon (ecoupon).
    รองรับชำระด้วย บัตรเครดิต/เดบิต (card), PromptPay (promptpay), e-Wallet/TrueWallet (truewallet).
    """
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Stripe not configured (STRIPE_SECRET_KEY)")
    amount_baht = body.amount
    if amount_baht < 20:
        raise HTTPException(status_code=400, detail="Minimum amount 20 THB")
    amount_satang = int(round(amount_baht * 100))
    metadata = {
        "customer_id": str(customer.id),
        "type": "member_" + body.intent_type,
    }
    pm = body.payment_method
    if pm == "card":
        payment_method_types = ["card"]
    elif pm == "promptpay":
        payment_method_types = ["promptpay"]
    elif pm == "truewallet":
        payment_method_types = ["truewallet"]
    else:
        payment_method_types = ["card"]
    return_url = (BACKEND_URL or "").rstrip("/") + "/member/dashboard"
    try:
        pi = stripe_promptpay.create_payment_intent(
            secret_key=STRIPE_SECRET_KEY,
            amount_satang=amount_satang,
            payment_method_types=payment_method_types,
            currency="thb",
            metadata=metadata,
            return_url=return_url,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "client_secret": pi.get("client_secret"),
        "payment_intent_id": pi.get("id"),
        "amount": amount_baht,
        "intent_type": body.intent_type,
        "payment_method": pm,
    }


# --- Activities (ประวัติการใช้งาน) ---
@router.get("/activities")
def list_my_activities(
    limit: int = 50,
    customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db),
):
    rows = db.query(MemberActivity).filter(MemberActivity.customer_id == customer.id).order_by(MemberActivity.id.desc()).limit(limit).all()
    return [{"id": r.id, "activity_type": r.activity_type, "amount": r.amount, "description": r.description, "created_at": r.created_at.isoformat() if r.created_at else None} for r in rows]
