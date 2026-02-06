"""
Store API - ระบบจัดการร้านค้า
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.models import Store, Menu
from app.utils.store_token import generate_store_token
from app.services.promptpay import (
    generate_promptpay_qr_image,
    generate_promptpay_credit_transfer_image
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


@router.get("/{store_id}")
async def get_store(store_id: int, db: Session = Depends(get_db)):
    """
    ดึงข้อมูลร้านค้า
    """
    try:
        from app.models import Profile, Event
        
        store = db.query(Store).filter(Store.id == store_id).first()
        if not store:
            raise HTTPException(status_code=404, detail="Store not found")
        
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
            "name": store.name,
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


class GeneratePromptPayQRRequest(BaseModel):
    menu_id: Optional[int] = None
    ref3: Optional[str] = None  # remark
    amount: float  # Total Price
    promptpay_mobile: Optional[str] = None  # สำหรับ Tag29 (Credit Transfer)
    promptpay_national_id: Optional[str] = None  # สำหรับ Tag29 (Credit Transfer)


@router.post("/{store_id}/generate-promptpay-qr")
async def generate_promptpay_qr(
    store_id: int,
    request: GeneratePromptPayQRRequest,
    db: Session = Depends(get_db)
):
    """
    สร้าง PromptPay QR Code (Tag30 - Bill Payment)
    
    - biller_id: store.biller_id (ถ้ามี) ไม่เช่นนั้น tax_id + "99"
    - ref1: store.token (20 หลัก)
    - ref2: menu.id (ถ้ามี)
    - ref3: remark (ถ้ามี)
    - amount: Total Price
    """
    # ดึงข้อมูลร้านค้า
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")

    # biller_id = store.biller_id หรือจาก tax_id + "99"
    if getattr(store, "biller_id", None) and store.biller_id.strip():
        biller_id = "".join(filter(str.isdigit, store.biller_id))[:15].zfill(15)
    else:
        if not store.tax_id:
            raise HTTPException(status_code=400, detail="Store tax_id or biller_id is required for PromptPay QR Code")
        tax_id_clean = "".join(filter(str.isdigit, store.tax_id))
        if not tax_id_clean:
            raise HTTPException(status_code=400, detail="Store tax_id must contain at least one digit")
        biller_id = (tax_id_clean + "99")
        if len(biller_id) < 15:
            biller_id = biller_id.zfill(15)
        elif len(biller_id) > 15:
            biller_id = biller_id[:15]

    # ref1 = store.token (20 หลัก)
    if getattr(store, "token", None) and store.token:
        ref1 = store.token
    else:
        ref1 = str(store.id)
    
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
    tax_id_clean = "".join(filter(str.isdigit, store.tax_id or ""))

    # สร้าง QR Code ทั้ง Tag29 และ Tag30 (static + dynamic)
    try:
        # Tag30 Static - Bill Payment (ไม่มี amount, สำหรับสแกนแล้วกรอกจำนวน)
        qr_image_tag30_static = generate_promptpay_qr_image(
            biller_id=biller_id,
            ref1=ref1,
            ref2=ref2,
            ref3=ref3,
            amount=None,
            size=300
        )
        # Tag30 Dynamic - Bill Payment (มี amount)
        qr_image_tag30 = generate_promptpay_qr_image(
            biller_id=biller_id,
            ref1=ref1,
            ref2=ref2,
            ref3=ref3,
            amount=amount,
            size=300
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
        
        return {
            "qr_code_tag30_static": qr_image_tag30_static,  # Tag30 ไม่มี amount (จาก store.biller_id, store.token)
            "qr_code_tag30": qr_image_tag30,  # Tag30 มี amount (Dynamic)
            "qr_code_tag29": qr_image_tag29,  # Credit Transfer (อาจเป็น None)
            "tag29_type": tag29_type,  # "mobile", "national_id", "national_id_from_tax", หรือ None
            "biller_id": biller_id,
            "ref1": ref1,
            "ref2": ref2,
            "ref3": ref3,
            "amount": amount
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating QR Code: {str(e)}")


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

    # biller_id = store.biller_id หรือจาก tax_id + "99"
    if getattr(store, "biller_id", None) and store.biller_id.strip():
        biller_id = "".join(filter(str.isdigit, store.biller_id))[:15].zfill(15)
    else:
        if not store.tax_id:
            raise HTTPException(status_code=400, detail="Store tax_id or biller_id is required for PromptPay QR Code")
        tax_id_clean = "".join(filter(str.isdigit, store.tax_id))
        if not tax_id_clean:
            raise HTTPException(status_code=400, detail="Store tax_id must contain at least one digit")
        biller_id = (tax_id_clean + "99")
        if len(biller_id) < 15:
            biller_id = biller_id.zfill(15)
        elif len(biller_id) > 15:
            biller_id = biller_id[:15]

    # ref1 = store.token (20 หลัก)
    if getattr(store, "token", None) and store.token:
        ref1 = store.token
    else:
        ref1 = str(store.id)

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

