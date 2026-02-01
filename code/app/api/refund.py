"""
Refund API - ระบบจัดการการคืนเงิน (Admin)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.refund_service import RefundService
from app.models import RefundRequest

router = APIRouter(prefix="/api/refunds", tags=["refunds"])


@router.get("/pending")
async def get_pending_refunds(db: Session = Depends(get_db)):
    """
    ดึงคำขอคืนเงินที่รอการประมวลผล
    """
    refund_service = RefundService(db)
    refund_requests = refund_service.get_pending_refund_requests()
    
    return [
        {
            "id": req.id,
            "customer_id": req.customer_id,
            "amount": req.amount,
            "refund_method": req.refund_method.value,
            "promptpay_number": req.promptpay_number,
            "status": req.status,
            "created_at": req.created_at.isoformat()
        }
        for req in refund_requests
    ]


@router.post("/{refund_request_id}/process")
async def process_refund(refund_request_id: int, db: Session = Depends(get_db)):
    """
    ประมวลผลการคืนเงิน
    """
    try:
        refund_service = RefundService(db)
        refund_request = refund_service.process_refund(refund_request_id)
        
        return {
            "id": refund_request.id,
            "status": refund_request.status,
            "amount": refund_request.amount,
            "refund_method": refund_request.refund_method.value,
            "processed_at": refund_request.processed_at.isoformat() if refund_request.processed_at else None
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/daily-reset")
async def trigger_daily_reset(db: Session = Depends(get_db)):
    """
    เรียกใช้ Daily Balance Reset (สำหรับ Cron Job)
    """
    try:
        refund_service = RefundService(db)
        refund_service.daily_balance_reset()
        
        return {
            "success": True,
            "message": "Daily balance reset completed"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notify/{customer_id}")
async def send_refund_notification(customer_id: int, db: Session = Depends(get_db)):
    """
    ส่งการแจ้งเตือนคืนเงินให้ลูกค้า
    """
    try:
        refund_service = RefundService(db)
        notification = refund_service.check_and_send_refund_notification(customer_id)
        
        if notification:
            return {
                "success": True,
                "notification_id": notification.id,
                "balance_amount": notification.balance_amount,
                "message": "Refund notification sent"
            }
        else:
            return {
                "success": False,
                "message": "No notification needed (no balance or e-Money license exists)"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

