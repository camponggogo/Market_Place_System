"""
Customer API - ระบบตรวจสอบยอดเงินและจัดการคืนเงิน
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.services.refund_service import RefundService
from app.models import Customer, CustomerBalance, RefundMethod
from app.models import RefundRequest as RefundRequestModel
import qrcode
from io import BytesIO
import base64

router = APIRouter(prefix="/api/customers", tags=["customers"])


class RegisterRequest(BaseModel):
    phone: str
    name: Optional[str] = None
    promptpay_number: Optional[str] = None


class RegisterResponse(BaseModel):
    id: int
    phone: str
    name: Optional[str]
    promptpay_number: Optional[str]
    created_at: str


class BalanceCheckRequest(BaseModel):
    qr_code: str


class BalanceResponse(BaseModel):
    customer_id: int
    phone: Optional[str]
    name: Optional[str]
    balance: float
    has_pending_refund: bool


class RefundRequest(BaseModel):
    customer_id: int
    amount: float
    refund_method: str  # "cash" or "promptpay"
    promptpay_number: Optional[str] = None


class RefundResponse(BaseModel):
    refund_request_id: int
    status: str
    amount: float
    refund_method: str
    message: str


@router.post("/register", response_model=RegisterResponse)
async def register_customer(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    ลงทะเบียนลูกค้าใหม่ และผูก Food Court ID ที่ว่าง หรือสร้างใหม่
    """
    try:
        # ตรวจสอบว่ามีลูกค้าอยู่แล้วหรือไม่
        existing_customer = db.query(Customer).filter(Customer.phone == request.phone).first()
        if existing_customer:
            raise HTTPException(status_code=400, detail="เบอร์โทรศัพท์นี้ถูกใช้งานแล้ว")
        
        # สร้างลูกค้าใหม่
        new_customer = Customer(
            phone=request.phone,
            name=request.name,
            promptpay_number=request.promptpay_number
        )
        db.add(new_customer)
        db.commit()
        db.refresh(new_customer)
        
        # สร้าง CustomerBalance
        balance = CustomerBalance(customer_id=new_customer.id, balance=0.0)
        db.add(balance)
        db.commit()
        
        # หา Food Court ID ที่ว่าง (ไม่มี customer_id และ status = active)
        from app.models import FoodCourtID
        from app.models import PaymentMethod
        
        empty_fc_id = db.query(FoodCourtID).filter(
            FoodCourtID.customer_id.is_(None),
            FoodCourtID.status == "active"
        ).first()
        
        if empty_fc_id:
            # ผูก Food Court ID ที่ว่างกับลูกค้า
            empty_fc_id.customer_id = new_customer.id
            db.commit()
        else:
            # สร้าง Food Court ID ใหม่ (ยอดเงิน 0)
            from app.services.payment_hub import PaymentHub
            from app.models import PaymentMethod
            payment_hub = PaymentHub(db)
            
            # สร้าง Food Court ID ใหม่ด้วยยอดเงิน 0
            new_fc_id = payment_hub.exchange_to_foodcourt_id(
                amount=0.0,
                payment_method=PaymentMethod.CASH,
                customer_id=new_customer.id
            )
        
        return RegisterResponse(
            id=new_customer.id,
            phone=new_customer.phone,
            name=new_customer.name,
            promptpay_number=new_customer.promptpay_number,
            created_at=new_customer.created_at.isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error registering customer: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check-balance", response_model=BalanceResponse)
async def check_balance(request: BalanceCheckRequest, db: Session = Depends(get_db)):
    """
    ตรวจสอบยอดเงินผ่าน QR Code
    """
    try:
        # Decode QR Code (อาจเป็น transaction_id หรือ customer_id)
        # TODO: Implement QR Code decoding logic
        qr_data = request.qr_code
        
        # ตัวอย่าง: ถ้า QR Code เป็น transaction_id
        # transaction = db.query(Transaction).filter(Transaction.qr_code == qr_data).first()
        # customer_id = transaction.customer_id
        
        # สำหรับตอนนี้ ใช้ customer_id โดยตรง (ควร decode จาก QR)
        # ในระบบจริงควรมี logic decode QR Code ที่เหมาะสม
        customer_id = int(qr_data)  # Temporary - should decode properly
        
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        refund_service = RefundService(db)
        balance = refund_service.get_customer_balance(customer_id)
        
        if not balance:
            # สร้าง balance ถ้ายังไม่มี
            balance = CustomerBalance(customer_id=customer_id, balance=0.0)
            db.add(balance)
            db.commit()
            db.refresh(balance)

        # ตรวจสอบว่ามีคำขอคืนเงินที่รออยู่หรือไม่
        pending_refund = db.query(RefundRequestModel).filter(
            RefundRequestModel.customer_id == customer_id,
            RefundRequestModel.status == "pending"
        ).first()

        return BalanceResponse(
            customer_id=customer.id,
            phone=customer.phone,
            name=customer.name,
            balance=balance.balance,
            has_pending_refund=pending_refund is not None
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{customer_id}/balance", response_model=BalanceResponse)
async def get_balance(customer_id: int, db: Session = Depends(get_db)):
    """
    ดึงยอดเงินคงเหลือของลูกค้า
    """
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    refund_service = RefundService(db)
    balance = refund_service.get_customer_balance(customer_id)
    
    if not balance:
        balance = CustomerBalance(customer_id=customer_id, balance=0.0)
        db.add(balance)
        db.commit()
        db.refresh(balance)

    pending_refund = db.query(RefundRequestModel).filter(
        RefundRequestModel.customer_id == customer_id,
        RefundRequestModel.status == "pending"
    ).first()

    return BalanceResponse(
        customer_id=customer.id,
        phone=customer.phone,
        name=customer.name,
        balance=balance.balance,
        has_pending_refund=pending_refund is not None
    )


@router.post("/refund", response_model=RefundResponse)
async def request_refund(request: RefundRequest, db: Session = Depends(get_db)):
    """
    สร้างคำขอคืนเงิน (Self-Service Refund)
    """
    try:
        refund_service = RefundService(db)
        
        # Validate refund method
        try:
            refund_method = RefundMethod(request.refund_method)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid refund method. Must be 'cash' or 'promptpay'"
            )

        # Create refund request
        refund_request = refund_service.create_refund_request(
            customer_id=request.customer_id,
            amount=request.amount,
            refund_method=refund_method,
            promptpay_number=request.promptpay_number
        )

        message = "คำขอคืนเงินถูกสร้างเรียบร้อยแล้ว"
        if refund_method == RefundMethod.CASH:
            message += " กรุณาไปรับเงินสดที่เคาน์เตอร์"
        elif refund_method == RefundMethod.PROMPTPAY:
            message += " เงินจะถูกโอนคืนผ่าน PromptPay ภายใน 1-2 วันทำการ"

        return RefundResponse(
            refund_request_id=refund_request.id,
            status=refund_request.status,
            amount=refund_request.amount,
            refund_method=refund_request.refund_method.value,
            message=message
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{customer_id}/refund-requests")
async def get_refund_requests(customer_id: int, db: Session = Depends(get_db)):
    """
    ดึงรายการคำขอคืนเงินของลูกค้า
    """
    refund_requests = db.query(RefundRequestModel).filter(
        RefundRequestModel.customer_id == customer_id
    ).order_by(RefundRequestModel.created_at.desc()).all()

    return [
        {
            "id": req.id,
            "amount": req.amount,
            "refund_method": req.refund_method.value,
            "status": req.status,
            "created_at": req.created_at.isoformat(),
            "processed_at": req.processed_at.isoformat() if req.processed_at else None
        }
        for req in refund_requests
    ]


@router.post("/generate-qr/{customer_id}")
async def generate_qr_code(customer_id: int, db: Session = Depends(get_db)):
    """
    สร้าง QR Code สำหรับตรวจสอบยอดเงิน
    """
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # สร้าง QR Code ที่มีข้อมูล customer_id หรือ transaction_id
    qr_data = f"{customer_id}"  # หรือใช้ transaction_id ถ้ามี
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return {
        "qr_code": f"data:image/png;base64,{img_str}",
        "qr_data": qr_data
    }

