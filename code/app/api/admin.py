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
    Customer, Store, BankingProfile,
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


# --- Banking Profiles (ตั้งค่า Bank API ต่อ group / site / store) ---

class BankingProfileCreate(BaseModel):
    name: str
    scope_type: str  # "group" | "site" | "store"
    group_id: Optional[int] = None
    site_id: Optional[int] = None
    store_id: Optional[int] = None
    provider_type: Optional[str] = None  # k_api | scb_deeplink | omise | mpay | stripe
    scb_app_name: Optional[str] = None
    scb_api_key: Optional[str] = None
    scb_api_secret: Optional[str] = None
    scb_callback_url: Optional[str] = None
    scb_webhook_secret: Optional[str] = None
    kbank_customer_id: Optional[str] = None
    kbank_consumer_secret: Optional[str] = None
    kbank_webhook_secret: Optional[str] = None
    omise_public_key: Optional[str] = None
    omise_secret_key: Optional[str] = None
    omise_webhook_secret: Optional[str] = None
    stripe_secret_key: Optional[str] = None
    stripe_publishable_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None
    mpay_merchant_id: Optional[str] = None
    mpay_api_key: Optional[str] = None
    mpay_webhook_secret: Optional[str] = None
    is_active: bool = True


class BankingProfileUpdate(BaseModel):
    name: Optional[str] = None
    scope_type: Optional[str] = None
    group_id: Optional[int] = None
    site_id: Optional[int] = None
    store_id: Optional[int] = None
    provider_type: Optional[str] = None
    scb_app_name: Optional[str] = None
    scb_api_key: Optional[str] = None
    scb_api_secret: Optional[str] = None
    scb_callback_url: Optional[str] = None
    scb_webhook_secret: Optional[str] = None
    kbank_customer_id: Optional[str] = None
    kbank_consumer_secret: Optional[str] = None
    kbank_webhook_secret: Optional[str] = None
    omise_public_key: Optional[str] = None
    omise_secret_key: Optional[str] = None
    omise_webhook_secret: Optional[str] = None
    stripe_secret_key: Optional[str] = None
    stripe_publishable_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None
    mpay_merchant_id: Optional[str] = None
    mpay_api_key: Optional[str] = None
    mpay_webhook_secret: Optional[str] = None
    is_active: Optional[bool] = None


def resolve_banking_profile_for_store(db: Session, store: Store):
    """
    หา BankingProfile สำหรับร้าน: store > site > group
    """
    if not store:
        return None
    # 1) ต่อร้าน (store)
    p = db.query(BankingProfile).filter(
        BankingProfile.is_active == True,
        BankingProfile.store_id == store.id,
    ).first()
    if p:
        return p
    # 2) ต่อ site
    p = db.query(BankingProfile).filter(
        BankingProfile.is_active == True,
        BankingProfile.scope_type == "site",
        BankingProfile.site_id == store.site_id,
        BankingProfile.store_id.is_(None),
    ).first()
    if p:
        return p
    # 3) ต่อ group
    p = db.query(BankingProfile).filter(
        BankingProfile.is_active == True,
        BankingProfile.scope_type == "group",
        BankingProfile.group_id == store.group_id,
        BankingProfile.site_id.is_(None),
        BankingProfile.store_id.is_(None),
    ).first()
    return p


@router.get("/banking-profiles")
async def list_banking_profiles(db: Session = Depends(get_db)):
    """รายการ Banking Profiles ทั้งหมด"""
    rows = db.query(BankingProfile).order_by(BankingProfile.scope_type, BankingProfile.group_id, BankingProfile.site_id, BankingProfile.store_id).all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "scope_type": r.scope_type,
            "group_id": r.group_id,
            "site_id": r.site_id,
            "store_id": r.store_id,
            "provider_type": getattr(r, "provider_type", None),
            "scb_app_name": r.scb_app_name,
            "scb_callback_url": r.scb_callback_url,
            "kbank_customer_id": (r.kbank_customer_id[:16] + "..." if r.kbank_customer_id and len(r.kbank_customer_id) > 16 else r.kbank_customer_id),
            "omise_public_key": (lambda v: (v[:16] + "...") if v and len(v) > 16 else v)(getattr(r, "omise_public_key", None)),
            "stripe_publishable_key": (lambda v: (v[:16] + "...") if v and len(v) > 16 else v)(getattr(r, "stripe_publishable_key", None)),
            "is_active": r.is_active,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


@router.get("/banking-profiles/resolve")
async def resolve_banking_profile(store_id: int, db: Session = Depends(get_db)):
    """หา profile ที่ใช้กับร้านนี้ (สำหรับ debug / แสดงใน UI)"""
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    profile = resolve_banking_profile_for_store(db, store)
    if not profile:
        return {"store_id": store_id, "profile": None, "message": "No banking profile matched (store/site/group)"}
    return {
        "store_id": store_id,
        "profile": {
            "id": profile.id,
            "name": profile.name,
            "scope_type": profile.scope_type,
        },
    }


@router.post("/banking-profiles", response_model=None)
async def create_banking_profile(body: BankingProfileCreate, db: Session = Depends(get_db)):
    """สร้าง Banking Profile"""
    p = BankingProfile(
        name=body.name,
        scope_type=body.scope_type,
        group_id=body.group_id,
        site_id=body.site_id,
        store_id=body.store_id,
        provider_type=body.provider_type,
        scb_app_name=body.scb_app_name,
        scb_api_key=body.scb_api_key,
        scb_api_secret=body.scb_api_secret,
        scb_callback_url=body.scb_callback_url,
        scb_webhook_secret=body.scb_webhook_secret,
        kbank_customer_id=body.kbank_customer_id,
        kbank_consumer_secret=body.kbank_consumer_secret,
        kbank_webhook_secret=body.kbank_webhook_secret,
        omise_public_key=body.omise_public_key,
        omise_secret_key=body.omise_secret_key,
        omise_webhook_secret=body.omise_webhook_secret,
        stripe_secret_key=body.stripe_secret_key,
        stripe_publishable_key=body.stripe_publishable_key,
        stripe_webhook_secret=body.stripe_webhook_secret,
        mpay_merchant_id=body.mpay_merchant_id,
        mpay_api_key=body.mpay_api_key,
        mpay_webhook_secret=body.mpay_webhook_secret,
        is_active=body.is_active,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return {"id": p.id, "name": p.name, "message": "Created"}


@router.get("/banking-profiles/{profile_id}")
async def get_banking_profile(profile_id: int, db: Session = Depends(get_db)):
    """ดึงรายละเอียด Banking Profile (รวม secret สำหรับแก้ไข; แสดงแบบ mask ใน list)"""
    p = db.query(BankingProfile).filter(BankingProfile.id == profile_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Banking profile not found")
    return {
        "id": p.id,
        "name": p.name,
        "scope_type": p.scope_type,
        "group_id": p.group_id,
        "site_id": p.site_id,
        "store_id": p.store_id,
        "provider_type": getattr(p, "provider_type", None),
        "scb_app_name": p.scb_app_name,
        "scb_api_key": p.scb_api_key,
        "scb_api_secret": p.scb_api_secret,
        "scb_callback_url": p.scb_callback_url,
        "scb_webhook_secret": p.scb_webhook_secret,
        "kbank_customer_id": p.kbank_customer_id,
        "kbank_consumer_secret": p.kbank_consumer_secret,
        "kbank_webhook_secret": p.kbank_webhook_secret,
        "omise_public_key": getattr(p, "omise_public_key", None),
        "omise_secret_key": getattr(p, "omise_secret_key", None),
        "omise_webhook_secret": getattr(p, "omise_webhook_secret", None),
        "stripe_secret_key": getattr(p, "stripe_secret_key", None),
        "stripe_publishable_key": getattr(p, "stripe_publishable_key", None),
        "stripe_webhook_secret": getattr(p, "stripe_webhook_secret", None),
        "mpay_merchant_id": getattr(p, "mpay_merchant_id", None),
        "mpay_api_key": getattr(p, "mpay_api_key", None),
        "mpay_webhook_secret": getattr(p, "mpay_webhook_secret", None),
        "is_active": p.is_active,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }


@router.put("/banking-profiles/{profile_id}")
async def update_banking_profile(profile_id: int, body: BankingProfileUpdate, db: Session = Depends(get_db)):
    """อัปเดต Banking Profile"""
    p = db.query(BankingProfile).filter(BankingProfile.id == profile_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Banking profile not found")
    if body.name is not None:
        p.name = body.name
    if body.scope_type is not None:
        p.scope_type = body.scope_type
    if body.group_id is not None:
        p.group_id = body.group_id
    if body.site_id is not None:
        p.site_id = body.site_id
    if body.store_id is not None:
        p.store_id = body.store_id
    if body.provider_type is not None:
        p.provider_type = body.provider_type
    if body.scb_app_name is not None:
        p.scb_app_name = body.scb_app_name
    if body.scb_api_key is not None:
        p.scb_api_key = body.scb_api_key
    if body.scb_api_secret is not None:
        p.scb_api_secret = body.scb_api_secret
    if body.scb_callback_url is not None:
        p.scb_callback_url = body.scb_callback_url
    if body.scb_webhook_secret is not None:
        p.scb_webhook_secret = body.scb_webhook_secret
    if body.kbank_customer_id is not None:
        p.kbank_customer_id = body.kbank_customer_id
    if body.kbank_consumer_secret is not None:
        p.kbank_consumer_secret = body.kbank_consumer_secret
    if body.kbank_webhook_secret is not None:
        p.kbank_webhook_secret = body.kbank_webhook_secret
    if body.omise_public_key is not None:
        p.omise_public_key = body.omise_public_key
    if body.omise_secret_key is not None:
        p.omise_secret_key = body.omise_secret_key
    if body.omise_webhook_secret is not None:
        p.omise_webhook_secret = body.omise_webhook_secret
    if body.stripe_secret_key is not None:
        p.stripe_secret_key = body.stripe_secret_key
    if body.stripe_publishable_key is not None:
        p.stripe_publishable_key = body.stripe_publishable_key
    if body.stripe_webhook_secret is not None:
        p.stripe_webhook_secret = body.stripe_webhook_secret
    if body.mpay_merchant_id is not None:
        p.mpay_merchant_id = body.mpay_merchant_id
    if body.mpay_api_key is not None:
        p.mpay_api_key = body.mpay_api_key
    if body.mpay_webhook_secret is not None:
        p.mpay_webhook_secret = body.mpay_webhook_secret
    if body.is_active is not None:
        p.is_active = body.is_active
    db.commit()
    return {"id": p.id, "message": "Updated"}


@router.delete("/banking-profiles/{profile_id}")
async def delete_banking_profile(profile_id: int, db: Session = Depends(get_db)):
    """ลบ Banking Profile"""
    p = db.query(BankingProfile).filter(BankingProfile.id == profile_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Banking profile not found")
    db.delete(p)
    db.commit()
    return {"message": "Deleted"}

