"""
Payment Hub API - ระบบจัดการการชำระเงิน
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.services.payment_hub import PaymentHub
from app.models import PaymentMethod

router = APIRouter(prefix="/api/payment-hub", tags=["payment-hub"])


class UseFoodCourtIDRequest(BaseModel):
    foodcourt_id: str
    store_id: int
    amount: float


@router.post("/use")
async def use_foodcourt_id(
    request: UseFoodCourtIDRequest,
    db: Session = Depends(get_db)
):
    """
    ใช้ Food Court ID ที่ร้านค้า (หักยอดเงิน)
    """
    try:
        payment_hub = PaymentHub(db)
        result = payment_hub.use_foodcourt_id(
            foodcourt_id_str=request.foodcourt_id,
            store_id=request.store_id,
            amount=request.amount
        )

        return {
            "success": True,
            **result
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
    payment_hub = PaymentHub(db)
    balance_info = payment_hub.get_foodcourt_id_balance(foodcourt_id)

    if not balance_info:
        raise HTTPException(status_code=404, detail="Food Court ID not found")

    return balance_info

