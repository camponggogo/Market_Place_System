"""
Reports API - ระบบรายงานและบัญชี
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
from app.database import get_db
from app.services.tax_service import TaxService
from app.services.refund_service import RefundService

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/sales-tax")
async def get_sales_tax_report(
    start_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    """
    รายงานภาษีขาย (Sales Tax Report)
    """
    try:
        # Default to last month if not provided
        if not end_date:
            end_date = datetime.now()
        else:
            end_date = datetime.fromisoformat(end_date)
        
        if not start_date:
            start_date = end_date - timedelta(days=30)
        else:
            start_date = datetime.fromisoformat(start_date)

        tax_service = TaxService(db)
        report = tax_service.generate_sales_tax_report(start_date, end_date)
        
        return report
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/separation-of-funds")
async def get_separation_of_funds_report(
    start_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    """
    รายงานแยกยอดเงินสด/โอน (Revenue) ออกจากยอด Crypto Status (Information Only)
    """
    try:
        if not end_date:
            end_date = datetime.now()
        else:
            end_date = datetime.fromisoformat(end_date)
        
        if not start_date:
            start_date = end_date - timedelta(days=30)
        else:
            start_date = datetime.fromisoformat(start_date)

        tax_service = TaxService(db)
        report = tax_service.get_separation_of_funds_report(start_date, end_date)
        
        return report
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/refund-summary")
async def get_refund_summary(
    start_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    """
    รายงานสรุปการคืนเงิน
    """
    try:
        if not end_date:
            end_date = datetime.now()
        else:
            end_date = datetime.fromisoformat(end_date)
        
        if not start_date:
            start_date = end_date - timedelta(days=30)
        else:
            start_date = datetime.fromisoformat(start_date)

        from app.models import RefundRequest
        refund_requests = db.query(RefundRequest).filter(
            RefundRequest.created_at >= start_date,
            RefundRequest.created_at <= end_date
        ).all()

        total_amount = sum(req.amount for req in refund_requests)
        cash_count = sum(1 for req in refund_requests if req.refund_method.value == "cash")
        promptpay_count = sum(1 for req in refund_requests if req.refund_method.value == "promptpay")
        
        pending_count = sum(1 for req in refund_requests if req.status == "pending")
        completed_count = sum(1 for req in refund_requests if req.status == "completed")
        failed_count = sum(1 for req in refund_requests if req.status == "failed")

        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "summary": {
                "total_requests": len(refund_requests),
                "total_amount": round(total_amount, 2),
                "by_method": {
                    "cash": {
                        "count": cash_count,
                        "amount": round(sum(req.amount for req in refund_requests if req.refund_method.value == "cash"), 2)
                    },
                    "promptpay": {
                        "count": promptpay_count,
                        "amount": round(sum(req.amount for req in refund_requests if req.refund_method.value == "promptpay"), 2)
                    }
                },
                "by_status": {
                    "pending": pending_count,
                    "completed": completed_count,
                    "failed": failed_count
                }
            },
            "requests": [
                {
                    "id": req.id,
                    "customer_id": req.customer_id,
                    "amount": req.amount,
                    "refund_method": req.refund_method.value,
                    "status": req.status,
                    "created_at": req.created_at.isoformat(),
                    "processed_at": req.processed_at.isoformat() if req.processed_at else None
                }
                for req in refund_requests
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/wht-calculation")
async def calculate_wht(
    amount: float,
    db: Session = Depends(get_db)
):
    """
    คำนวณภาษีหัก ณ ที่จ่าย (Withholding Tax) 3%
    """
    tax_service = TaxService(db)
    wht_calc = tax_service.calculate_wht(amount)
    
    return wht_calc


@router.get("/vat-calculation")
async def calculate_vat(
    amount: float,
    db: Session = Depends(get_db)
):
    """
    คำนวณภาษีมูลค่าเพิ่ม (VAT) 7%
    """
    tax_service = TaxService(db)
    vat_calc = tax_service.calculate_vat(amount)
    
    return vat_calc

