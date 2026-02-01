"""
Payment Callback API - รับ Back Transaction จากธนาคาร, รายงาน, รายการโอนสิ้นวัน, แจ้งร้าน
อ้างอิง SCB Developers: https://developer.scb/ - QR Payment (แจ้งร้านเมื่อชำระเสร็จ), Slip Verification
"""
from datetime import datetime, date
from typing import Optional, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.settlement_service import (
    receive_back_transaction,
    get_back_transactions_report,
    create_daily_settlements,
    get_settlement_list,
    mark_settlement_transferred,
    notify_store_settlement,
    get_store_settlements_for_receipt,
    get_recent_paid_for_store,
)
from app.api.signage import set_signage_paid

router = APIRouter(prefix="/api/payment-callback", tags=["payment-callback"])


# --- Request/Response models ---

class BackTransactionPayload(BaseModel):
    """Payload จาก Webhook/Callback ธนาคาร (SCB QR Payment ฯลฯ)"""
    ref1: str          # store token (20 หลัก)
    amount: float
    paid_at: Optional[str] = None  # ISO datetime ถ้าไม่มีใช้เวลาปัจจุบัน
    ref2: Optional[str] = None
    ref3: Optional[str] = None
    slip_reference: Optional[str] = None
    bank_account: Optional[str] = None  # เลขที่บัญชี
    raw_payload: Optional[Any] = None


class SettlementNotifyRequest(BaseModel):
    settlement_id: int


# --- Endpoints ---

@router.get("/webhook")
async def webhook_health():
    """
    ให้ธนาคาร/ระบบภายนอกตรวจสอบว่า Webhook endpoint ยังทำงาน (health check)
    ใช้ตอนลงทะเบียน Webhook URL กับ SCB/ธนาคาร
    """
    return {"status": "ok", "message": "Webhook endpoint is ready"}


@router.post("/back-transaction")
async def post_back_transaction(
    payload: BackTransactionPayload,
    db: Session = Depends(get_db),
):
    """
    รับข้อมูล Back Transaction จากธนาคาร (Webhook/Callback)
    ใช้ ref1 (store token), ref2, ref3, ยอดเงิน, เวลาโอน เก็บไว้ทำ Report
    """
    try:
        paid_at = datetime.utcnow()
        if payload.paid_at:
            paid_at = datetime.fromisoformat(payload.paid_at.replace("Z", "+00:00"))
        raw = None
        if payload.raw_payload is not None:
            import json
            raw = json.dumps(payload.raw_payload) if isinstance(payload.raw_payload, dict) else str(payload.raw_payload)
        back = receive_back_transaction(
            db=db,
            ref1=payload.ref1,
            amount=payload.amount,
            paid_at=paid_at,
            ref2=payload.ref2,
            ref3=payload.ref3,
            slip_reference=payload.slip_reference,
            bank_account=payload.bank_account,
            raw_payload=raw,
        )
        if back.store_id:
            set_signage_paid(back.store_id)
        return {
            "id": back.id,
            "ref1": back.ref1,
            "ref2": back.ref2,
            "ref3": back.ref3,
            "amount": back.amount,
            "paid_at": back.paid_at.isoformat() if back.paid_at else None,
            "store_id": back.store_id,
            "status": back.status,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/webhook")
async def webhook_receive(
    payload: BackTransactionPayload,
    db: Session = Depends(get_db),
):
    """
    Webhook URL สำหรับลงทะเบียนกับธนาคาร (SCB QR Payment ฯลฯ)
    เมื่อลูกค้าชำระเงิน ธนาคารจะส่ง POST มาที่ URL นี้
    URL ที่ลงทะเบียน: https://your-domain.com/api/payment-callback/webhook
    """
    return await post_back_transaction(payload=payload, db=db)


@router.get("/back-transactions/report")
async def report_back_transactions(
    store_id: Optional[int] = Query(None),
    start_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    limit: int = Query(500, le=2000),
    db: Session = Depends(get_db),
):
    """รายงาน Back Transactions สำหรับทำ Report (ใช้ ref1, ref2, ref3, ยอด, เวลา)"""
    start = datetime.fromisoformat(start_date + "T00:00:00") if start_date else None
    end = datetime.fromisoformat(end_date + "T23:59:59") if end_date else None
    rows = get_back_transactions_report(db, store_id=store_id, start_date=start, end_date=end, limit=limit)
    return {"items": rows, "count": len(rows)}


@router.get("/settlements")
async def list_settlements(
    settlement_date: Optional[str] = Query(None, description="YYYY-MM-DD สิ้นวันที่ต้องการดู"),
    status: Optional[str] = Query(None, description="pending / transferred / notified"),
    db: Session = Depends(get_db),
):
    """
    รายการเตรียมโอนเงินไปยังลูกค้า (ร้านค้า) สิ้นวัน
    ข้อกำหนดกฏหมาย: ถือฝากได้แค่ 1 วัน
    """
    d = date.fromisoformat(settlement_date) if settlement_date else None
    items = get_settlement_list(db, settlement_date=d, status=status)
    return {"items": items, "count": len(items)}


@router.post("/settlements/create-daily")
async def create_daily_settlements_endpoint(
    settlement_date: Optional[str] = Query(None, description="YYYY-MM-DD ไม่ส่งใช้วันนี้"),
    db: Session = Depends(get_db),
):
    """สร้างรายการโอนสิ้นวันจาก Back Transactions ของวันนั้น (เรียกจาก Scheduler หรือมือ)"""
    d = date.fromisoformat(settlement_date) if settlement_date else None
    created = create_daily_settlements(db, settlement_date=d)
    return {
        "created": len(created),
        "items": [
            {"id": s.id, "store_id": s.store_id, "amount": s.amount, "settlement_date": s.settlement_date.isoformat() if s.settlement_date else None}
            for s in created
        ],
    }


@router.post("/settlements/{settlement_id}/mark-transferred")
async def mark_transferred(
    settlement_id: int,
    db: Session = Depends(get_db),
):
    """บันทึกว่าโอนเงินให้ร้านแล้ว"""
    st = mark_settlement_transferred(db, settlement_id)
    if not st:
        raise HTTPException(status_code=404, detail="Settlement not found")
    return {"id": st.id, "status": st.status, "transferred_at": st.transferred_at.isoformat() if st.transferred_at else None}


@router.post("/settlements/{settlement_id}/notify-store")
async def notify_store(
    settlement_id: int,
    db: Session = Depends(get_db),
):
    """
    แจ้งร้านว่าเงินเข้าเรียบร้อยแล้ว
    ร้านสามารถพิมพ์ใบเสร็จรับเงินมอบให้ลูกค้าได้
    """
    st = notify_store_settlement(db, settlement_id)
    if not st:
        raise HTTPException(status_code=404, detail="Settlement not found")
    return {
        "id": st.id,
        "store_id": st.store_id,
        "status": st.status,
        "notified_at": st.notified_at.isoformat() if st.notified_at else None,
        "message": "แจ้งร้านเรียบร้อยแล้ว สามารถพิมพ์ใบเสร็จรับเงินได้",
    }


@router.get("/stores/{store_id}/recent-paid")
async def store_recent_paid(
    store_id: int,
    since: Optional[str] = Query(None, description="ISO datetime ใช้ดึงรายการที่จ่ายหลังเวลานี้ (store-pos ใช้ poll)"),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
):
    """
    รายการที่จ่ายเงินแล้วของร้าน (สำหรับ store-pos แจ้งเตือน + ออกเสียง "เงินเข้าแล้ว X บาท ขอบคุณครับ")
    store-pos เรียก poll ด้วย since=เวลาล่าสุดที่เช็คแล้ว
    """
    since_dt = datetime.fromisoformat(since.replace("Z", "+00:00")) if since else None
    items = get_recent_paid_for_store(db, store_id=store_id, since=since_dt, limit=limit)
    return {"items": items, "count": len(items)}


@router.get("/stores/{store_id}/settlements-for-receipt")
async def store_settlements_for_receipt(
    store_id: int,
    notified_only: bool = Query(True, description="แสดงเฉพาะที่แจ้งแล้ว (เงินเข้าเรียบร้อย)"),
    db: Session = Depends(get_db),
):
    """รายการที่ร้านสามารถพิมพ์ใบเสร็จรับเงินได้ (เงินเข้าเรียบร้อยแล้ว)"""
    items = get_store_settlements_for_receipt(db, store_id=store_id, notified_only=notified_only)
    return {"items": items, "count": len(items)}
