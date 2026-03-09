"""
Payment Reports API - ระบบรายงานสรุปยอด
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
from app.database import get_db
from app.services.report_service import ReportService
from app.services.settlement_service import get_settlement_summary_by_period

router = APIRouter(prefix="/api/reports/payment", tags=["reports-payment"])


def _parse_period(period_type: Optional[str], date_str: Optional[str], year: Optional[int], month: Optional[int], start_date: Optional[str], end_date: Optional[str]):
    """คืนค่า (start_dt, end_dt) ตาม period_type หรือ start_date/end_date"""
    now = datetime.now()
    today = now.date()

    if start_date and end_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00")).replace(tzinfo=None)
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00")).replace(tzinfo=None)
            if end_dt.hour == 0 and end_dt.minute == 0:
                end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
            return start_dt, end_dt
        except (ValueError, TypeError):
            pass

    if period_type == "day" and date_str:
        try:
            d = datetime.fromisoformat(date_str).date()
            start_dt = datetime.combine(d, datetime.min.time())
            end_dt = datetime.combine(d, datetime.max.time())
            return start_dt, end_dt
        except (ValueError, TypeError):
            pass

    if period_type == "week" and date_str:
        try:
            d = datetime.fromisoformat(date_str).date()
            # จันทร์ = 0 ใน Python weekday
            start_week = d - timedelta(days=d.weekday())
            end_week = start_week + timedelta(days=6)
            start_dt = datetime.combine(start_week, datetime.min.time())
            end_dt = datetime.combine(end_week, datetime.max.time())
            return start_dt, end_dt
        except (ValueError, TypeError):
            pass

    if period_type == "month" and year is not None and month is not None:
        start_dt = datetime(year, month, 1)
        if month == 12:
            end_dt = datetime(year + 1, 1, 1) - timedelta(seconds=1)
        else:
            end_dt = datetime(year, month + 1, 1) - timedelta(seconds=1)
        return start_dt, end_dt

    if period_type == "year" and year is not None:
        start_dt = datetime(year, 1, 1)
        end_dt = datetime(year, 12, 31, 23, 59, 59)
        return start_dt, end_dt

    # default: today
    start_dt = datetime.combine(today, datetime.min.time())
    end_dt = datetime.combine(today, datetime.max.time())
    return start_dt, end_dt


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


@router.get("/settlement-summary")
async def get_settlement_summary(
    start_date: Optional[str] = Query(None, description="YYYY-MM-DD (ช่วงเวลา)"),
    end_date: Optional[str] = Query(None, description="YYYY-MM-DD (ช่วงเวลา)"),
    period_type: Optional[str] = Query(None, description="day | week | month | year (ใช้คู่กับ date หรือ year/month)"),
    date: Optional[str] = Query(None, description="YYYY-MM-DD สำหรับ period_type=day|week"),
    year: Optional[int] = Query(None, description="ปี สำหรับ period_type=month|year"),
    month: Optional[int] = Query(None, description="เดือน 1-12 สำหรับ period_type=month"),
    gp_percent: Optional[float] = Query(None, description="อัตราหัก GP % (ว่าง = ใช้จาก config)"),
    db: Session = Depends(get_db),
):
    """
    สรุปยอดรายวัน/สัปดาห์/เดือน/ปี/ช่วงเวลาที่เลือก แยกร้านค้าทั้งหมดในครั้งเดียว
    fields: ลำดับ, store_id, ชื่อร้าน, เลขที่บัญชีร้าน, ยอดเงินที่จะโอนให้ร้าน, ยอดหัก GP
    และสรุปรวม: ยอดขายรวม, GP รวม, ยอดโอนรวม
    """
    try:
        start_dt, end_dt = _parse_period(period_type, date, year, month, start_date, end_date)
        by_store, overall = get_settlement_summary_by_period(db, start_dt, end_dt, gp_percent)
        return {
            "period": {
                "start_date": start_dt.isoformat(),
                "end_date": end_dt.isoformat(),
            },
            "by_store": by_store,
            "overall": overall,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/overall-summary")
async def get_overall_summary(
    start_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    period_type: Optional[str] = Query(None, description="day | week | month | year"),
    date: Optional[str] = Query(None, description="YYYY-MM-DD สำหรับ day|week"),
    year: Optional[int] = Query(None, description="ปี สำหรับ month|year"),
    month: Optional[int] = Query(None, description="เดือน 1-12 สำหรับ month"),
    db: Session = Depends(get_db),
):
    """
    สรุปรายได้ ยอดขาย GP รวม รายวัน/สัปดาห์/เดือน/ปี/ช่วงเวลาที่เลือก
    """
    try:
        start_dt, end_dt = _parse_period(period_type, date, year, month, start_date, end_date)
        _, overall = get_settlement_summary_by_period(db, start_dt, end_dt, None)
        return {
            "period": {"start_date": start_dt.isoformat(), "end_date": end_dt.isoformat()},
            "total_sales": overall["total_sales"],
            "total_gp": overall["total_gp"],
            "total_transfer": overall["total_transfer"],
            "gp_percent": overall["gp_percent"],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

