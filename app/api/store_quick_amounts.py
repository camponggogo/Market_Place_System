"""
Store Quick Amounts API - จัดการราคาด่วนสำหรับแต่ละร้านค้า
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from app.database import get_db
from app.models import Store, StoreQuickAmount

router = APIRouter(prefix="/api/stores/{store_id}/quick-amounts", tags=["store-quick-amounts"])


class QuickAmountCreate(BaseModel):
    amount: float
    label: Optional[str] = None
    display_order: Optional[int] = 0


class QuickAmountUpdate(BaseModel):
    amount: Optional[float] = None
    label: Optional[str] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None


class QuickAmountResponse(BaseModel):
    id: int
    store_id: int
    amount: float
    label: Optional[str]
    display_order: int
    is_active: bool

    class Config:
        from_attributes = True


@router.get("/", response_model=List[QuickAmountResponse])
async def get_quick_amounts(store_id: int, db: Session = Depends(get_db)):
    """
    ดึงรายการราคาด่วนของร้านค้า
    """
    # ตรวจสอบว่า store มีอยู่จริง
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    
    # ดึง quick amounts ที่ active และเรียงตาม display_order
    quick_amounts = db.query(StoreQuickAmount).filter(
        StoreQuickAmount.store_id == store_id,
        StoreQuickAmount.is_active == True
    ).order_by(StoreQuickAmount.display_order, StoreQuickAmount.amount).all()
    
    return quick_amounts


@router.post("/", response_model=QuickAmountResponse)
async def create_quick_amount(
    store_id: int,
    quick_amount: QuickAmountCreate,
    db: Session = Depends(get_db)
):
    """
    สร้างราคาด่วนใหม่
    """
    # ตรวจสอบว่า store มีอยู่จริง
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    
    # ตรวจสอบว่า amount > 0
    if quick_amount.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be greater than 0")
    
    # สร้าง quick amount ใหม่
    new_quick_amount = StoreQuickAmount(
        store_id=store_id,
        amount=quick_amount.amount,
        label=quick_amount.label or f"{quick_amount.amount:.0f} บาท",
        display_order=quick_amount.display_order or 0
    )
    
    db.add(new_quick_amount)
    db.commit()
    db.refresh(new_quick_amount)
    
    return new_quick_amount


@router.put("/{quick_amount_id}", response_model=QuickAmountResponse)
async def update_quick_amount(
    store_id: int,
    quick_amount_id: int,
    quick_amount: QuickAmountUpdate,
    db: Session = Depends(get_db)
):
    """
    อัปเดตราคาด่วน
    """
    # ตรวจสอบว่า store มีอยู่จริง
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    
    # ดึง quick amount
    existing = db.query(StoreQuickAmount).filter(
        StoreQuickAmount.id == quick_amount_id,
        StoreQuickAmount.store_id == store_id
    ).first()
    
    if not existing:
        raise HTTPException(status_code=404, detail="Quick amount not found")
    
    # อัปเดตข้อมูล
    if quick_amount.amount is not None:
        if quick_amount.amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be greater than 0")
        existing.amount = quick_amount.amount
    
    if quick_amount.label is not None:
        existing.label = quick_amount.label
    
    if quick_amount.display_order is not None:
        existing.display_order = quick_amount.display_order
    
    if quick_amount.is_active is not None:
        existing.is_active = quick_amount.is_active
    
    db.commit()
    db.refresh(existing)
    
    return existing


@router.delete("/{quick_amount_id}")
async def delete_quick_amount(
    store_id: int,
    quick_amount_id: int,
    db: Session = Depends(get_db)
):
    """
    ลบราคาด่วน (soft delete โดยตั้ง is_active = False)
    """
    # ตรวจสอบว่า store มีอยู่จริง
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    
    # ดึง quick amount
    existing = db.query(StoreQuickAmount).filter(
        StoreQuickAmount.id == quick_amount_id,
        StoreQuickAmount.store_id == store_id
    ).first()
    
    if not existing:
        raise HTTPException(status_code=404, detail="Quick amount not found")
    
    # Soft delete
    existing.is_active = False
    db.commit()
    
    return {"message": "Quick amount deleted successfully"}

