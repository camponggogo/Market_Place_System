"""
Payment Reports API - ระบบรายงานสรุปยอด
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
from app.database import get_db
from app.services.report_service import ReportService

router = APIRouter(prefix="/api/reports/payment", tags=["reports-payment"])


@router.get("/store/{store_id}")
async def get_store_summary(
    store_id: int,
    start_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    profile_id: Optional[int] = Query(None),
    event_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """
    สรุปยอดรายร้านค้า
    """
    try:
        report_service = ReportService(db)
        
        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None
        
        summary = report_service.get_store_summary(store_id, start, end, profile_id, event_id)
        return summary
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/daily")
async def get_daily_summary(
    date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    """
    สรุปยอดรายวัน
    """
    try:
        report_service = ReportService(db)
        
        target_date = datetime.fromisoformat(date) if date else None
        summary = report_service.get_daily_summary(target_date)
        return summary
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/monthly")
async def get_monthly_summary(
    year: int = Query(..., description="Year (e.g., 2024)"),
    month: int = Query(..., description="Month (1-12)"),
    db: Session = Depends(get_db)
):
    """
    สรุปยอดรายเดือน
    """
    try:
        if month < 1 or month > 12:
            raise HTTPException(status_code=400, detail="Month must be between 1 and 12")
        
        report_service = ReportService(db)
        summary = report_service.get_monthly_summary(year, month)
        return summary
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/yearly")
async def get_yearly_summary(
    year: int = Query(..., description="Year (e.g., 2024)"),
    db: Session = Depends(get_db)
):
    """
    สรุปยอดรายปี
    """
    try:
        report_service = ReportService(db)
        summary = report_service.get_yearly_summary(year)
        return summary
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

