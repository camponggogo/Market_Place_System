"""
Store API - ระบบจัดการร้านค้า
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import json
from app.database import get_db
from app.models import Store, Menu, Order, StoreLocaleSetting
from app.utils.i18n import resolve_i18n
from app.utils.store_token import generate_store_token
from app.services.promptpay import (
    generate_promptpay_qr_image,
    generate_promptpay_qr_content,
    generate_promptpay_credit_transfer_image,
)
from app.services.promptpay_bot_standard import (
    generate_bot_standard_qr_362,
    generate_bot_standard_qr_62,
    generate_bot_qr_image
)

router = APIRouter(prefix="/api/stores", tags=["stores"])


class StoreCreate(BaseModel):
    name: str
    tax_id: str = None
    group_id: int = 0   # 3 digits สำหรับ token
    site_id: int = 0    # 4 digits สำหรับ token
    biller_id: Optional[str] = None  # PromptPay Biller ID 15 หลัก


class StoreUpdate(BaseModel):
    """อัปเดต site_id / group_id (จัดลำดับ Site > Group > Store)"""
    site_id: Optional[int] = None
    group_id: Optional[int] = None


class StoreResponse(BaseModel):
    id: int
    name: str
    tax_id: str = None
    crypto_enabled: bool
    contract_accepted: bool
    token: Optional[str] = None
    biller_id: Optional[str] = None


@router.post("/", response_model=StoreResponse)
async def create_store(store: StoreCreate, db: Session = Depends(get_db)):
    """
    สร้างร้านค้าใหม่ และสร้าง token 20 หลัก (group_id 3 + site_id 4 + store_id 6 + menu_id 7)
    """
    new_store = Store(
        name=store.name,
        tax_id=store.tax_id,
        crypto_enabled=False,
        contract_accepted=False,
        group_id=store.group_id,
        site_id=store.site_id,
        biller_id=store.biller_id,
    )
    db.add(new_store)
    db.commit()
    db.refresh(new_store)

    # สร้าง token ประจำร้าน 20 หลัก (menu_id=0 ระดับร้าน)
    new_store.token = generate_store_token(
        group_id=new_store.group_id,
        site_id=new_store.site_id,
        store_id=new_store.id,
        menu_id=0,
    )
    db.commit()
    db.refresh(new_store)

    return StoreResponse(
        id=new_store.id,
        name=new_store.name,
        tax_id=new_store.tax_id,
        crypto_enabled=new_store.crypto_enabled,
        contract_accepted=new_store.contract_accepted,
        token=new_store.token,
        biller_id=new_store.biller_id,
    )


def _get_store_locale(db: Session, store_id: int) -> str:
    row = db.query(StoreLocaleSetting).filter(StoreLocaleSetting.store_id == store_id).first()
    return row.locale if row else "th"


@router.get("/{store_id}")
async def get_store(
    store_id: int,
    locale: Optional[str] = Query(None, description="ภาษา - ไม่ระบุใช้ตามร้าน"),
    db: Session = Depends(get_db)
):
    """
    ดึงข้อมูลร้านค้า (name ตาม locale)
    """
    try:
        from app.models import Profile, Event
        
        store = db.query(Store).filter(Store.id == store_id).first()
        if not store:
            raise HTTPException(status_code=404, detail="Store not found")
        
        loc = locale or _get_store_locale(db, store_id)
        name_i18n = getattr(store, "name_i18n", None)
        store_name = resolve_i18n(name_i18n, store.name, loc) or store.name
        
        # Get profile and event names if available
        profile_name = None
        event_name = None
        
        try:
            if store.profile_id:
                profile = db.query(Profile).filter(Profile.id == store.profile_id).first()
                profile_name = profile.name if profile else None
        except Exception:
            # Profile table might not exist yet
            profile_name = None
        
        try:
            if store.event_id:
                event = db.query(Event).filter(Event.id == store.event_id).first()
                event_name = event.name if event else None
        except Exception:
            # Event table might not exist yet
            event_name = None
        
        return {
            "id": store.id,
            "name": store_name,
            "tax_id": store.tax_id,
            "crypto_enabled": store.crypto_enabled,
            "contract_accepted": store.contract_accepted,
            "token": store.token,
            "biller_id": getattr(store, "biller_id", None),
            "group_id": getattr(store, "group_id", 0),
            "site_id": getattr(store, "site_id", 0),
            "location_name": store.location_name,
            "latitude": store.latitude,
            "longitude": store.longitude,
            "profile_id": store.profile_id,
            "event_id": store.event_id,
            "profile_name": profile_name,
            "event_name": event_name
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading store: {str(e)}")


@router.get("/")
async def list_stores(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    ดึงรายการร้านค้าทั้งหมด (รวม group_id, site_id สำหรับ Admin จัด Site/Group/Store)
    """
    stores = db.query(Store).offset(skip).limit(limit).all()
    
    return [
        {
            "id": store.id,
            "name": store.name,
            "tax_id": store.tax_id,
            "crypto_enabled": store.crypto_enabled,
            "contract_accepted": store.contract_accepted,
            "token": getattr(store, "token", None),
            "biller_id": getattr(store, "biller_id", None),
            "group_id": getattr(store, "group_id", 0),
            "site_id": getattr(store, "site_id", 0),
        }
        for store in stores
    ]


@router.patch("/{store_id}")
async def update_store(
    store_id: int,
    body: StoreUpdate,
    db: Session = Depends(get_db),
):
    """
    อัปเดต site_id / group_id ของร้าน (และสร้าง token ใหม่)
    """
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    if body.site_id is not None:
        store.site_id = body.site_id
    if body.group_id is not None:
        store.group_id = body.group_id
    store.token = generate_store_token(
        group_id=store.group_id,
        site_id=store.site_id,
        store_id=store.id,
        menu_id=0,
    )
    db.commit()
    db.refresh(store)
    return {
        "id": store.id,
        "name": store.name,
        "group_id": store.group_id,
        "site_id": store.site_id,
        "token": store.token,
    }


class OrderLineItem(BaseModel):
    menu_id: int
    name: str
    qty: int
    unit_price: float


class GeneratePromptPayQRRequest(BaseModel):
    amount: float  # Total Price
    order_lines: Optional[list] = None  # [{ menu_id, name, qty, unit_price }] สำหรับเก็บ order และใช้ ref2=order_id
    ref3: Optional[str] = None  # remark
    promptpay_mobile: Optional[str] = None  # สำหรับ Tag29 (Credit Transfer)
    promptpay_national_id: Optional[str] = None  # สำหรับ Tag29 (Credit Transfer)


@router.post("/{store_id}/generate-promptpay-qr")
async def generate_promptpay_qr(
    store_id: int,
    request: GeneratePromptPayQRRequest,
    db: Session = Depends(get_db),
    debug: bool = Query(False, description="เมื่อเปิด จะส่ง qr_content_tag30 กลับมาเพื่อตรวจสอบ/ดีบัก"),
):
    """
    สร้าง PromptPay QR Code (Tag30 - Bill Payment)
    ใช้ logic เดียวกับ Run/qr_code_web.py หน้า /qr-code?store_id=X&amount=... (ที่สแกนผ่านแล้ว)

    - biller_id: ควรเป็น Biller ID ที่ธนาคารออกให้ (store.biller_id); ถ้าไม่มี ใช้ tax_id + "99" เป็น fallback
    - ref1: ตัวเลขเท่านั้น 20 หลัก (จาก store.token แค่ตัวเลข หรือ store.id ปัดศูนย์) ให้สแกนได้
    - ref2: order_id (สร้าง Order เก็บรายการแล้วใช้ id เป็น ref2 สำหรับสืบค้นย้อนหลัง)
    - ref3: remark (ถ้ามี)
    - amount: Total Price
    """
    # ดึงข้อมูลร้านค้า
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")

    # biller_id ต้องเป็นเลขที่ธนาคารออกให้ (ลงทะเบียน Bill Payment) แอปธนาคารจึงจะรับ QR ได้; ถ้าไม่มี ใช้ tax_id+"99" เป็น fallback (อาจทำให้แอปแจ้ง "QR ไม่ถูกต้อง")
    biller_id_source = "registered"
    if getattr(store, "biller_id", None) and store.biller_id.strip():
        b = "".join(filter(str.isdigit, store.biller_id))
        if len(b) == 15:
            biller_id = b
        elif len(b) == 13:
            biller_id = b + "99"
        else:
            biller_id = b.zfill(15)[:15]
    else:
        biller_id_source = "tax_id_fallback"
        if not store.tax_id:
            raise HTTPException(status_code=400, detail="Store tax_id or biller_id is required for PromptPay QR Code")
        tax_id_clean = "".join(filter(str.isdigit, store.tax_id))
        if not tax_id_clean:
            raise HTTPException(status_code=400, detail="Store tax_id must contain at least one digit")
        tax_id_13 = (tax_id_clean.zfill(13))[:13]
        biller_id = tax_id_13 + "99"

    # ref1 สำหรับ Tag30 ควรเป็นตัวเลขเท่านั้น (แอปธนาคารส่วนใหญ่รับเฉพาะ numeric) ให้ตรงกับรูปแบบที่ SCAN PASS
    _token = (getattr(store, "token", None) or "").strip()
    _digits_only = "".join(c for c in _token if c.isdigit())
    if _digits_only and len(_digits_only) >= 1:
        ref1 = _digits_only.zfill(20)[:20]
    else:
        ref1 = (str(store.id) or "").zfill(20)[:20]

    # สร้าง Order เก็บรายการแล้วใช้ order.id เป็น ref2 (สำหรับสืบค้นย้อนหลังและจับคู่เมื่อเงินเข้า)
    order_lines = request.order_lines or []
    order = Order(
        store_id=store_id,
        total_amount=request.amount,
        status="pending",
        items=json.dumps(order_lines, ensure_ascii=False) if order_lines else None,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    # ref2 = order_id ใน QR เป็นตัวเลข 12 หลัก (ปัดศูนย์) เพื่อให้แอปธนาคารยอมรับได้; callback ส่ง ref2 กลับมา ใช้ int(ref2) จับคู่ Order
    ref2 = str(order.id).zfill(12)[:12]
    ref3 = (request.ref3 or "").strip() or None
    if ref3:
        ref3 = ref3[:27]

    # amount = Total Price
    amount = request.amount
    tax_id_clean = "".join(filter(str.isdigit, store.tax_id or ""))

    # สร้าง QR Code Tag30 (มี ref2=order_id, ref3 ตามที่ส่งมา)
    try:
        # Tag30 Static - Bill Payment (ไม่มี amount)
        qr_image_tag30_static = generate_promptpay_qr_image(
            biller_id=biller_id,
            ref1=ref1,
            ref2=ref2,
            ref3=ref3,
            amount=None,
            merchant_name="NA",
            merchant_city="BANGKOK",
            size=300,
        )
        # Tag30 Dynamic - Bill Payment (มี amount)
        qr_image_tag30 = generate_promptpay_qr_image(
            biller_id=biller_id,
            ref1=ref1,
            ref2=ref2,
            ref3=ref3,
            amount=amount,
            merchant_name="NA",
            merchant_city="BANGKOK",
            size=300,
        )
        
        # Tag29 - Credit Transfer (ถ้ามี mobile หรือ national_id)
        qr_image_tag29 = None
        tag29_type = None
        
        # ลองใช้ mobile number ก่อน
        if request.promptpay_mobile:
            try:
                qr_image_tag29 = generate_promptpay_credit_transfer_image(
                    mobile_number=request.promptpay_mobile,
                    amount=amount,
                    size=300
                )
                tag29_type = "mobile"
            except Exception as e:
                # ถ้า mobile ไม่ถูกต้อง ลองใช้ national_id
                pass
        
        # ถ้ายังไม่มี QR29 และมี national_id
        if not qr_image_tag29 and request.promptpay_national_id:
            try:
                qr_image_tag29 = generate_promptpay_credit_transfer_image(
                    national_id=request.promptpay_national_id,
                    amount=amount,
                    size=300
                )
                tag29_type = "national_id"
            except Exception as e:
                pass
        
        # ถ้ายังไม่มี QR29 ลองใช้ tax_id เป็น national_id (ถ้าเป็น 13 หลัก)
        if not qr_image_tag29 and tax_id_clean and len(tax_id_clean) == 13:
            try:
                qr_image_tag29 = generate_promptpay_credit_transfer_image(
                    national_id=tax_id_clean,
                    amount=amount,
                    size=300
                )
                tag29_type = "national_id_from_tax"
            except Exception as e:
                pass
        
        out = {
            "qr_code_tag30_static": qr_image_tag30_static,
            "qr_code_tag30": qr_image_tag30,
            "qr_code_tag29": qr_image_tag29,
            "tag29_type": tag29_type,
            "order_id": order.id,
            "ref2": ref2,
            "ref3": ref3,
            "biller_id": biller_id,
            "biller_id_source": biller_id_source,
            "ref1": ref1,
            "amount": amount,
            "biller_id_note": "ถ้าแอปธนาคารแจ้ง 'QR ไม่ถูกต้อง' ให้ลงทะเบียน Biller ID กับธนาคารแล้วใส่ในร้าน (biller_id). ตอนนี้ใช้: " + ("Biller ID ลงทะเบียนแล้ว" if biller_id_source == "registered" else "tax_id+99 (อาจไม่รับจากแอปธนาคาร)"),
        }
        if debug:
            qr_content_tag30 = generate_promptpay_qr_content(
                biller_id=biller_id,
                ref1=ref1,
                ref2=ref2,
                ref3=ref3,
                amount=amount,
                merchant_name="NA",
                merchant_city="BANGKOK",
            )
            out["qr_content_tag30"] = qr_content_tag30
        return out
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating QR Code: {str(e)}")


class CreateOrderRequest(BaseModel):
    amount: float
    order_lines: Optional[list] = None  # [{ menu_id, name, qty, unit_price }]


@router.post("/{store_id}/orders")
async def create_store_order(
    store_id: int,
    body: CreateOrderRequest,
    db: Session = Depends(get_db),
):
    """สร้าง Order เฉพาะ (สำหรับ Gateway เช่น Omise Credit/Debit) คืน order_id"""
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    order = Order(
        store_id=store_id,
        total_amount=body.amount,
        status="pending",
        items=json.dumps(body.order_lines or [], ensure_ascii=False),
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return {"order_id": order.id}


@router.get("/{store_id}/orders")
async def list_store_orders(
    store_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = Query(None, description="pending, paid, cancelled"),
    db: Session = Depends(get_db),
):
    """รายการ order ของร้าน (สำหรับสืบค้นย้อนหลัง)"""
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    q = db.query(Order).filter(Order.store_id == store_id)
    if status:
        q = q.filter(Order.status == status)
    orders = q.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
    return [
        {
            "id": o.id,
            "store_id": o.store_id,
            "total_amount": o.total_amount,
            "status": o.status,
            "items": json.loads(o.items) if o.items else [],
            "created_at": o.created_at.isoformat() if o.created_at else None,
            "paid_at": o.paid_at.isoformat() if o.paid_at else None,
        }
        for o in orders
    ]


@router.get("/{store_id}/orders/{order_id}")
async def get_store_order(
    store_id: int,
    order_id: int,
    db: Session = Depends(get_db),
):
    """ดึง order ตาม id (สำหรับสืบค้นย้อนหลัง)"""
    order = db.query(Order).filter(Order.id == order_id, Order.store_id == store_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return {
        "id": order.id,
        "store_id": order.store_id,
        "total_amount": order.total_amount,
        "status": order.status,
        "items": json.loads(order.items) if order.items else [],
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "paid_at": order.paid_at.isoformat() if order.paid_at else None,
    }


class GenerateBOTStandardQRRequest(BaseModel):
    """Request สำหรับสร้าง QR Code ตามมาตรฐาน BOT"""
    menu_id: Optional[int] = None
    ref3: Optional[str] = None  # remark
    amount: float  # Total Price
    promptpay_mobile: Optional[str] = None  # สำหรับ Tag29 (Credit Transfer)
    promptpay_national_id: Optional[str] = None  # สำหรับ Tag29 (Credit Transfer)
    # ข้อมูลผู้ซื้อ (สำหรับแบบ 362 ตัวอักษร)
    buyer_name: Optional[str] = None
    buyer_address: Optional[str] = None
    buyer_city: Optional[str] = None
    buyer_province: Optional[str] = None
    buyer_postcode: Optional[str] = None
    buyer_country: Optional[str] = None
    type_of_income: Optional[str] = None  # รหัสประเภทเงินได้พึงประเมิน (3 หลัก)


@router.post("/{store_id}/generate-bot-standard-qr")
async def generate_bot_standard_qr(
    store_id: int,
    request: GenerateBOTStandardQRRequest,
    db: Session = Depends(get_db)
):
    """
    สร้าง PromptPay QR Code ตามมาตรฐาน BOT ทั้ง 4 แบบ:
    - biller_id: store.biller_id
    - ref1: store.token (20 หลัก)
    อ้างอิง: https://www.bot.or.th/content/dam/bot/fipcs/documents/FPG/2562/ThaiPDF/25620084.pdf
    """
    # ดึงข้อมูลร้านค้า
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")

    # biller_id ต้องเป็นเลขที่ธนาคารออกให้ (ลงทะเบียน Bill Payment) จึงจะจ่ายเงินได้; ถ้าไม่มี ใช้ tax_id+"99" เป็น fallback
    if getattr(store, "biller_id", None) and store.biller_id.strip():
        b = "".join(filter(str.isdigit, store.biller_id))
        if len(b) == 15:
            biller_id = b
        elif len(b) == 13:
            biller_id = b + "99"
        else:
            biller_id = b.zfill(15)[:15]
    else:
        if not store.tax_id:
            raise HTTPException(status_code=400, detail="Store tax_id or biller_id is required for PromptPay QR Code")
        tax_id_clean = "".join(filter(str.isdigit, store.tax_id))
        if not tax_id_clean:
            raise HTTPException(status_code=400, detail="Store tax_id must contain at least one digit")
        tax_id_13 = (tax_id_clean.zfill(13))[:13]
        biller_id = tax_id_13 + "99"

    # ref1 สำหรับ Tag30 ควรเป็นตัวเลขเท่านั้น (แอปธนาคารส่วนใหญ่รับเฉพาะ numeric)
    _token = (getattr(store, "token", None) or "").strip()
    _digits_only = "".join(c for c in _token if c.isdigit())
    if _digits_only and len(_digits_only) >= 1:
        ref1 = _digits_only.zfill(20)[:20]
    else:
        ref1 = (str(store.id) or "").zfill(20)[:20]

    tax_id_clean = "".join(filter(str.isdigit, store.tax_id or ""))
    
    # ref2 = menu.id (ถ้ามี)
    ref2 = None
    if request.menu_id:
        menu = db.query(Menu).filter(Menu.id == request.menu_id, Menu.store_id == store_id).first()
        if not menu:
            raise HTTPException(status_code=404, detail="Menu not found")
        ref2 = str(menu.id)
    
    # ref3 = remark (ถ้ามี)
    ref3 = request.ref3
    
    # amount = Total Price
    amount = request.amount
    
    qr_codes = {}
    
    try:
        # 1. Tag30 - Bill Payment แบบ 362 ตัวอักษร (แบบเต็ม)
        try:
            qr_content_362 = generate_bot_standard_qr_362(
                biller_id=biller_id,
                ref1=ref1,
                ref2=ref2,
                ref3=ref3,
                amount=amount,
                buyer_name=request.buyer_name,
                buyer_address=request.buyer_address,
                buyer_city=request.buyer_city,
                buyer_province=request.buyer_province,
                buyer_postcode=request.buyer_postcode,
                buyer_country=request.buyer_country,
                type_of_income=request.type_of_income
            )
            qr_codes["tag30_362"] = generate_bot_qr_image(qr_content_362)
            qr_codes["tag30_362_content"] = qr_content_362
            qr_codes["tag30_362_length"] = len(qr_content_362)
        except Exception as e:
            qr_codes["tag30_362"] = None
            qr_codes["tag30_362_error"] = str(e)
        
        # 2. Tag30 - Bill Payment แบบ 62 ตัวอักษร (แบบสั้น)
        try:
            qr_content_62 = generate_bot_standard_qr_62(
                biller_id=biller_id,
                ref1=ref1,
                ref2=ref2,
                ref3=ref3,
                amount=amount
            )
            qr_codes["tag30_62"] = generate_bot_qr_image(qr_content_62)
            qr_codes["tag30_62_content"] = qr_content_62
            qr_codes["tag30_62_length"] = len(qr_content_62)
        except Exception as e:
            qr_codes["tag30_62"] = None
            qr_codes["tag30_62_error"] = str(e)
        
        # 3. Tag30 - Bill Payment (แบบเดิม)
        try:
            qr_image_tag30 = generate_promptpay_qr_image(
                biller_id=biller_id,
                ref1=ref1,
                ref2=ref2,
                ref3=ref3,
                amount=amount
            )
            qr_codes["tag30_standard"] = qr_image_tag30
        except Exception as e:
            qr_codes["tag30_standard"] = None
            qr_codes["tag30_standard_error"] = str(e)
        
        # 4. Tag29 - Credit Transfer
        qr_image_tag29 = None
        tag29_type = None
        
        if request.promptpay_mobile:
            try:
                qr_image_tag29 = generate_promptpay_credit_transfer_image(
                    mobile_number=request.promptpay_mobile,
                    amount=amount
                )
                tag29_type = "mobile"
            except Exception as e:
                pass
        
        if not qr_image_tag29 and request.promptpay_national_id:
            try:
                qr_image_tag29 = generate_promptpay_credit_transfer_image(
                    national_id=request.promptpay_national_id,
                    amount=amount
                )
                tag29_type = "national_id"
            except Exception as e:
                pass
        
        if not qr_image_tag29 and tax_id_clean and len(tax_id_clean) == 13:
            try:
                qr_image_tag29 = generate_promptpay_credit_transfer_image(
                    national_id=tax_id_clean,
                    amount=amount
                )
                tag29_type = "national_id_from_tax"
            except Exception as e:
                pass
        
        qr_codes["tag29"] = qr_image_tag29
        qr_codes["tag29_type"] = tag29_type
        
        return {
            "qr_codes": qr_codes,
            "biller_id": biller_id,
            "ref1": ref1,
            "ref2": ref2,
            "ref3": ref3,
            "amount": amount
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating BOT Standard QR Code: {str(e)}")

