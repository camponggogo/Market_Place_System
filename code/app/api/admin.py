"""
Admin API - สำหรับ Admin Dashboard
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from app.database import get_db
from app.models import (
    FoodCourtID, Transaction, StoreTransaction, CounterTransaction,
    Customer, Store
)

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/statistics")
async def get_statistics(db: Session = Depends(get_db)):
    """
    ดึงสถิติรวมของระบบ
    """
    # นับ Food Court IDs ทั้งหมด
    total_fc_ids = db.query(FoodCourtID).count()
    
    # นับ Food Court IDs ที่ active
    active_fc_ids = db.query(FoodCourtID).filter(FoodCourtID.status == "active").count()
    
    # ยอดเงินรวมทั้งหมด
    total_amount = db.query(func.sum(FoodCourtID.initial_amount)).scalar() or 0.0
    
    # ยอดเงินคงเหลือทั้งหมด
    total_balance = db.query(func.sum(FoodCourtID.current_balance)).scalar() or 0.0
    
    # Transactions วันนี้
    today_start = datetime.combine(datetime.now().date(), datetime.min.time())
    today_transactions = db.query(StoreTransaction).filter(
        StoreTransaction.created_at >= today_start
    ).count()
    
    # ยอดขายวันนี้
    today_sales = db.query(func.sum(StoreTransaction.amount)).filter(
        StoreTransaction.created_at >= today_start,
        StoreTransaction.status == "completed"
    ).scalar() or 0.0
    
    # จำนวนลูกค้า
    total_customers = db.query(Customer).count()
    
    # จำนวนร้านค้า
    total_stores = db.query(Store).count()
    
    return {
        "foodcourt_ids": {
            "total": total_fc_ids,
            "active": active_fc_ids,
            "used": db.query(FoodCourtID).filter(FoodCourtID.status == "used").count(),
            "refunded": db.query(FoodCourtID).filter(FoodCourtID.status == "refunded").count()
        },
        "amounts": {
            "total_initial": round(total_amount, 2),
            "total_balance": round(total_balance, 2),
            "total_used": round(total_amount - total_balance, 2)
        },
        "today": {
            "transactions": today_transactions,
            "sales": round(today_sales, 2)
        },
        "customers": {
            "total": total_customers
        },
        "stores": {
            "total": total_stores
        }
    }


@router.get("/transactions")
async def list_transactions(
    skip: int = 0,
    limit: int = 100,
    store_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    ดึงรายการ Transactions ทั้งหมด
    """
    query = db.query(Transaction)
    
    if store_id:
        query = query.filter(Transaction.store_id == store_id)
    
    transactions = query.order_by(Transaction.created_at.desc()).offset(skip).limit(limit).all()
    
    return [
        {
            "id": t.id,
            "customer_id": t.customer_id,
            "store_id": t.store_id,
            "foodcourt_id": t.foodcourt_id,
            "amount": t.amount,
            "payment_method": t.payment_method.value,
            "status": t.status.value,
            "receipt_number": t.receipt_number,
            "created_at": t.created_at.isoformat()
        }
        for t in transactions
    ]


@router.get("/customers")
async def list_customers(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    ดึงรายการลูกค้าทั้งหมด
    """
    query = db.query(Customer)
    
    if search:
        query = query.filter(
            (Customer.name.contains(search)) |
            (Customer.phone.contains(search))
        )
    
    customers = query.order_by(Customer.created_at.desc()).offset(skip).limit(limit).all()
    
    # ดึงยอดเงินคงเหลือและ Food Court IDs
    from app.models import CustomerBalance, FoodCourtID
    
    result = []
    for customer in customers:
        balance = db.query(CustomerBalance).filter(
            CustomerBalance.customer_id == customer.id
        ).first()
        
        # นับจำนวน Food Court IDs ที่ผูกไว้
        fc_ids = db.query(FoodCourtID).filter(
            FoodCourtID.customer_id == customer.id
        ).all()
        
        result.append({
            "id": customer.id,
            "phone": customer.phone,
            "name": customer.name,
            "promptpay_number": customer.promptpay_number,
            "balance": balance.balance if balance else 0.0,
            "foodcourt_ids_count": len(fc_ids),
            "foodcourt_ids": [fc.foodcourt_id for fc in fc_ids],
            "created_at": customer.created_at.isoformat()
        })
    
    return result


class LinkFoodCourtIDRequest(BaseModel):
    customer_id: int
    foodcourt_id: Optional[str] = None  # ถ้าไม่ระบุจะสร้างใหม่


@router.post("/customers/link-foodcourt-id")
async def link_foodcourt_id(
    request: LinkFoodCourtIDRequest,
    db: Session = Depends(get_db)
):
    """
    ผูก Food Court ID กับลูกค้า
    ถ้าไม่ระบุ foodcourt_id จะหาที่ว่างหรือสร้างใหม่
    """
    try:
        from app.models import FoodCourtID, PaymentMethod
        from app.services.payment_hub import PaymentHub
        
        # ตรวจสอบว่าลูกค้ามีอยู่จริง
        customer = db.query(Customer).filter(Customer.id == request.customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        if request.foodcourt_id:
            # ผูกกับ Food Court ID ที่ระบุ
            fc_id = db.query(FoodCourtID).filter(
                FoodCourtID.foodcourt_id == request.foodcourt_id
            ).first()
            
            if not fc_id:
                raise HTTPException(status_code=404, detail="Food Court ID not found")
            
            if fc_id.customer_id and fc_id.customer_id != request.customer_id:
                raise HTTPException(status_code=400, detail="Food Court ID already linked to another customer")
            
            fc_id.customer_id = request.customer_id
            db.commit()
            
            return {
                "success": True,
                "message": f"Food Court ID {request.foodcourt_id} linked to customer {request.customer_id}",
                "foodcourt_id": fc_id.foodcourt_id
            }
        else:
            # หา Food Court ID ที่ว่าง
            empty_fc_id = db.query(FoodCourtID).filter(
                FoodCourtID.customer_id.is_(None),
                FoodCourtID.status == "active"
            ).first()
            
            if empty_fc_id:
                # ผูกกับ Food Court ID ที่ว่าง
                empty_fc_id.customer_id = request.customer_id
                db.commit()
                
                return {
                    "success": True,
                    "message": f"Food Court ID {empty_fc_id.foodcourt_id} linked to customer {request.customer_id}",
                    "foodcourt_id": empty_fc_id.foodcourt_id
                }
            else:
                # สร้าง Food Court ID ใหม่
                payment_hub = PaymentHub(db)
                new_fc_id = payment_hub.exchange_to_foodcourt_id(
                    amount=0.0,
                    payment_method=PaymentMethod.CASH,
                    customer_id=request.customer_id
                )
                
                return {
                    "success": True,
                    "message": f"New Food Court ID {new_fc_id.foodcourt_id} created and linked to customer {request.customer_id}",
                    "foodcourt_id": new_fc_id.foodcourt_id
                }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error linking Food Court ID: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/customers/{customer_id}/foodcourt-id/{foodcourt_id}")
async def unlink_foodcourt_id(
    customer_id: int,
    foodcourt_id: str,
    db: Session = Depends(get_db)
):
    """
    ยกเลิกการผูก Food Court ID กับลูกค้า
    """
    try:
        from app.models import FoodCourtID
        
        fc_id = db.query(FoodCourtID).filter(
            FoodCourtID.foodcourt_id == foodcourt_id,
            FoodCourtID.customer_id == customer_id
        ).first()
        
        if not fc_id:
            raise HTTPException(status_code=404, detail="Food Court ID not found or not linked to this customer")
        
        fc_id.customer_id = None
        db.commit()
        
        return {
            "success": True,
            "message": f"Food Court ID {foodcourt_id} unlinked from customer {customer_id}"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

