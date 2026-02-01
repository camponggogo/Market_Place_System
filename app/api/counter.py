"""
Counter API - ระบบแลก Food Court ID ที่ Counter
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json
from app.database import get_db
from app.services.payment_hub import PaymentHub
from app.models import PaymentMethod

router = APIRouter(prefix="/api/counter", tags=["counter"])


class ExchangeRequest(BaseModel):
    amount: float
    payment_method: str
    payment_details: Optional[Dict[str, Any]] = None
    counter_id: Optional[int] = None
    counter_user_id: Optional[int] = None
    customer_id: Optional[int] = None


class RefundRequest(BaseModel):
    foodcourt_id: str
    counter_id: Optional[int] = None
    counter_user_id: Optional[int] = None


class TopUpRequest(BaseModel):
    foodcourt_id: str
    amount: float
    payment_method: str
    payment_details: Optional[Dict[str, Any]] = None
    counter_id: Optional[int] = None
    counter_user_id: Optional[int] = None


@router.post("/exchange")
async def exchange_to_foodcourt_id(
    request: ExchangeRequest,
    db: Session = Depends(get_db)
):
    """
    แลก Food Court ID ที่ Counter
    รองรับทั้งรูปแบบที่ 1 (เงินสดเท่านั้น) และรูปแบบที่ 2 (หลายรูปแบบ)
    """
    try:
        # Validate payment method
        try:
            payment_method = PaymentMethod(request.payment_method)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid payment method. Available methods: {[m.value for m in PaymentMethod]}"
            )

        payment_hub = PaymentHub(db)
        foodcourt_id = payment_hub.exchange_to_foodcourt_id(
            amount=request.amount,
            payment_method=payment_method,
            payment_details=request.payment_details,
            counter_id=request.counter_id,
            counter_user_id=request.counter_user_id,
            customer_id=request.customer_id
        )

        return {
            "success": True,
            "foodcourt_id": foodcourt_id.foodcourt_id,
            "amount": foodcourt_id.initial_amount,
            "payment_method": foodcourt_id.payment_method.value,
            "created_at": foodcourt_id.created_at.isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/balance/{foodcourt_id}")
async def get_balance(
    foodcourt_id: str,
    db: Session = Depends(get_db)
):
    """
    ตรวจสอบยอดเงินคงเหลือของ Food Court ID
    """
    try:
        payment_hub = PaymentHub(db)
        balance_info = payment_hub.get_foodcourt_id_balance(foodcourt_id)

        if not balance_info:
            raise HTTPException(status_code=404, detail=f"Food Court ID not found: {foodcourt_id}")

        return balance_info
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting balance for {foodcourt_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/refund")
async def refund_remaining_balance(
    request: RefundRequest,
    db: Session = Depends(get_db)
):
    """
    คืนเงินที่เหลือที่ Counter
    """
    try:
        payment_hub = PaymentHub(db)
        refund_info = payment_hub.refund_remaining_balance(
            foodcourt_id_str=request.foodcourt_id,
            counter_id=request.counter_id,
            counter_user_id=request.counter_user_id
        )

        return {
            "success": True,
            **refund_info
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/payment-methods")
async def get_payment_methods(db: Session = Depends(get_db)):
    """
    ดึงรายการ Payment Methods ที่รองรับ
    """
    payment_hub = PaymentHub(db)
    
    methods = []
    for method in PaymentMethod:
        info = payment_hub.get_payment_method_info(method)
        methods.append({
            "code": method.value,
            **info
        })

    return {
        "payment_methods": methods
    }


@router.post("/topup")
async def topup_foodcourt_id(
    request: TopUpRequest,
    db: Session = Depends(get_db)
):
    """
    เติมเงินให้ Food Court ID ที่มีอยู่แล้ว
    """
    try:
        from app.models import FoodCourtID, CounterTransaction
        from datetime import datetime
        
        # Validate payment method
        try:
            payment_method = PaymentMethod(request.payment_method)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid payment method. Available methods: {[m.value for m in PaymentMethod]}"
            )
        
        # Validate amount
        if request.amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be greater than 0")
        
        # Find Food Court ID
        foodcourt_id = db.query(FoodCourtID).filter(
            FoodCourtID.foodcourt_id == request.foodcourt_id
        ).first()
        
        if not foodcourt_id:
            raise HTTPException(status_code=404, detail=f"Food Court ID not found: {request.foodcourt_id}")
        
        if foodcourt_id.status != "active":
            raise HTTPException(status_code=400, detail=f"Food Court ID is not active (status: {foodcourt_id.status})")
        
        # Add balance
        old_balance = foodcourt_id.current_balance
        foodcourt_id.current_balance += request.amount
        foodcourt_id.initial_amount += request.amount  # Update initial amount as well
        
        # Create counter transaction for topup
        counter_transaction = CounterTransaction(
            foodcourt_id=request.foodcourt_id,
            counter_id=request.counter_id or 0,
            counter_user_id=request.counter_user_id or 0,
            amount=request.amount,
            payment_method=payment_method,
            payment_details=json.dumps(request.payment_details) if request.payment_details else None,
            status="completed"
        )
        db.add(counter_transaction)
        db.commit()
        db.refresh(foodcourt_id)
        db.refresh(counter_transaction)
        
        return {
            "success": True,
            "foodcourt_id": foodcourt_id.foodcourt_id,
            "topup_amount": request.amount,
            "old_balance": old_balance,
            "new_balance": foodcourt_id.current_balance,
            "payment_method": payment_method.value,
            "transaction_id": counter_transaction.id,
            "created_at": counter_transaction.created_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error topping up {request.foodcourt_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/foodcourt-ids")
async def list_foodcourt_ids(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    customer_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    ดึงรายการ Food Court IDs ทั้งหมด
    """
    from app.models import FoodCourtID
    
    query = db.query(FoodCourtID)
    
    if customer_id:
        query = query.filter(FoodCourtID.customer_id == customer_id)
    
    if status:
        query = query.filter(FoodCourtID.status == status)
    
    foodcourt_ids = query.order_by(FoodCourtID.created_at.desc()).offset(skip).limit(limit).all()
    
    return [
        {
            "id": fc.id,
            "foodcourt_id": fc.foodcourt_id,
            "customer_id": fc.customer_id,
            "initial_amount": fc.initial_amount,
            "current_balance": fc.current_balance,
            "payment_method": fc.payment_method.value,
            "status": fc.status,
            "created_at": fc.created_at.isoformat(),
            "updated_at": fc.updated_at.isoformat() if fc.updated_at else None
        }
        for fc in foodcourt_ids
    ]

