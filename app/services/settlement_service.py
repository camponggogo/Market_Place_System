"""
Settlement Service - รับ Back Transaction, รายงาน, รายการโอนสิ้นวัน, แจ้งร้าน
อ้างอิง SCB Developers: https://developer.scb/ - QR Payment, Slip Verification
ข้อกำหนดกฏหมาย: ถือฝากเงินได้แค่ 1 วัน (เกิน = payment gateway ต้องขอใบอนุญาต)
"""
from datetime import datetime, date, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import (
    Store,
    Customer,
    Transaction,
    PromptPayBackTransaction,
    StoreSettlement,
    PaymentMethod,
    TransactionStatus,
)


def _get_or_create_promptpay_guest_customer(db: Session) -> Customer:
    """ลูกค้า placeholder สำหรับ Transaction จาก Webhook (ไม่มีลูกค้าจริง)"""
    guest = db.query(Customer).filter(Customer.phone == "PROMPTPAY-GUEST").first()
    if guest:
        return guest
    guest = Customer(phone="PROMPTPAY-GUEST", name="ลูกค้า PromptPay (QR)")
    db.add(guest)
    db.commit()
    db.refresh(guest)
    return guest


def receive_back_transaction(
    db: Session,
    ref1: str,
    amount: float,
    paid_at: datetime,
    ref2: Optional[str] = None,
    ref3: Optional[str] = None,
    slip_reference: Optional[str] = None,
    bank_account: Optional[str] = None,
    raw_payload: Optional[str] = None,
) -> PromptPayBackTransaction:
    """
    รับข้อมูล Back Transaction จากธนาคาร (Webhook/Callback)
    ใส่ DB ทันที: PromptPayBackTransaction + Transaction (อัปเดตสถานะจ่ายเงินแล้ว)
    ref1 = store token (20 หลัก), ref2 = menu/ref, ref3 = remark
    """
    store_id = None
    store = db.query(Store).filter(Store.token == ref1.strip()).first()
    if store:
        store_id = store.id

    back = PromptPayBackTransaction(
        ref1=ref1.strip(),
        ref2=ref2.strip() if ref2 else None,
        ref3=ref3.strip() if ref3 else None,
        amount=amount,
        paid_at=paid_at,
        slip_reference=slip_reference,
        bank_account=bank_account,
        store_id=store_id,
        status="received",
        raw_payload=raw_payload,
    )
    db.add(back)
    db.commit()
    db.refresh(back)

    # สร้าง/อัปเดต Transaction ในตาราง transactions (ref1, ref2, ref3, เลขที่บัญชี) และสถานะจ่ายเงินแล้ว
    guest = _get_or_create_promptpay_guest_customer(db)
    receipt_number = slip_reference or f"PP-{back.id}-{paid_at.strftime('%Y%m%d%H%M%S')}"
    # ตรวจสอบว่า receipt_number ไม่ซ้ำ
    existing = db.query(Transaction).filter(Transaction.receipt_number == receipt_number).first()
    if existing:
        receipt_number = f"PP-{back.id}-{back.created_at.strftime('%Y%m%d%H%M%S')}" if back.created_at else f"PP-{back.id}-{id(back)}"
    txn = Transaction(
        customer_id=guest.id,
        store_id=store_id or 1,  # fallback ถ้า ref1 ไม่ตรงร้านใด
        amount=amount,
        payment_method=PaymentMethod.PROMPTPAY,
        status=TransactionStatus.CONFIRMED,
        receipt_number=receipt_number,
        ref1=back.ref1,
        ref2=back.ref2,
        ref3=back.ref3,
        bank_account=bank_account,
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)
    return back


def get_recent_paid_for_store(
    db: Session,
    store_id: int,
    since: Optional[datetime] = None,
    limit: int = 50,
) -> List[dict]:
    """รายการที่จ่ายเงินแล้วของร้าน (สำหรับ store-pos แจ้งเตือน + ออกเสียง)"""
    q = (
        db.query(PromptPayBackTransaction)
        .filter(
            PromptPayBackTransaction.store_id == store_id,
            PromptPayBackTransaction.status == "received",
        )
        .order_by(PromptPayBackTransaction.paid_at.desc())
    )
    if since is not None:
        q = q.filter(PromptPayBackTransaction.paid_at >= since)
    rows = q.limit(limit).all()
    return [
        {
            "id": r.id,
            "amount": r.amount,
            "paid_at": r.paid_at.isoformat() if r.paid_at else None,
            "ref2": r.ref2,
            "ref3": r.ref3,
        }
        for r in rows
    ]


def get_back_transactions_report(
    db: Session,
    store_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 500,
) -> List[dict]:
    """รายงาน Back Transactions สำหรับทำ Report"""
    q = db.query(PromptPayBackTransaction).order_by(
        PromptPayBackTransaction.paid_at.desc()
    )
    if store_id is not None:
        q = q.filter(PromptPayBackTransaction.store_id == store_id)
    if start_date is not None:
        q = q.filter(PromptPayBackTransaction.paid_at >= start_date)
    if end_date is not None:
        q = q.filter(PromptPayBackTransaction.paid_at <= end_date)
    rows = q.limit(limit).all()
    return [
        {
            "id": r.id,
            "ref1": r.ref1,
            "ref2": r.ref2,
            "ref3": r.ref3,
            "amount": r.amount,
            "paid_at": r.paid_at.isoformat() if r.paid_at else None,
            "slip_reference": r.slip_reference,
            "store_id": r.store_id,
            "store_name": r.store.name if r.store else None,
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


def create_daily_settlements(db: Session, settlement_date: Optional[date] = None) -> List[StoreSettlement]:
    """
    สร้างรายการเตรียมโอนเงินไปยังร้านค้า สิ้นวัน
    รวมยอดจาก PromptPayBackTransaction ตาม ref1 (store) ที่ paid_at อยู่ในวันนั้น
    ข้อกำหนด: ถือฝากได้แค่ 1 วัน
    """
    if settlement_date is None:
        settlement_date = date.today()
    start = datetime.combine(settlement_date, datetime.min.time())
    end = datetime.combine(settlement_date, datetime.max.time())

    # รวมยอดต่อร้าน (store_id) จาก back_transactions ในวันนั้น
    subq = (
        db.query(
            PromptPayBackTransaction.store_id,
            func.sum(PromptPayBackTransaction.amount).label("total"),
        )
        .filter(
            PromptPayBackTransaction.paid_at >= start,
            PromptPayBackTransaction.paid_at <= end,
            PromptPayBackTransaction.store_id.isnot(None),
        )
        .group_by(PromptPayBackTransaction.store_id)
    )
    result = subq.all()
    created = []
    for store_id, total in result:
        if store_id is None or total <= 0:
            continue
        existing = (
            db.query(StoreSettlement)
            .filter(
                StoreSettlement.store_id == store_id,
                func.date(StoreSettlement.settlement_date) == settlement_date,
            )
            .first()
        )
        if existing:
            continue
        st = StoreSettlement(
            store_id=store_id,
            settlement_date=end,
            amount=float(total),
            status="pending",
        )
        db.add(st)
        created.append(st)
    db.commit()
    for st in created:
        db.refresh(st)
    return created


def get_settlement_list(
    db: Session,
    settlement_date: Optional[date] = None,
    status: Optional[str] = None,
) -> List[dict]:
    """รายการเตรียมโอนเงินสิ้นวัน (Schedule list)"""
    q = db.query(StoreSettlement).order_by(StoreSettlement.store_id)
    if settlement_date is not None:
        q = q.filter(func.date(StoreSettlement.settlement_date) == settlement_date)
    if status is not None:
        q = q.filter(StoreSettlement.status == status)
    rows = q.all()
    return [
        {
            "id": r.id,
            "store_id": r.store_id,
            "store_name": r.store.name if r.store else None,
            "store_token": r.store.token if r.store else None,
            "settlement_date": r.settlement_date.isoformat() if r.settlement_date else None,
            "amount": r.amount,
            "status": r.status,
            "transferred_at": r.transferred_at.isoformat() if r.transferred_at else None,
            "notified_at": r.notified_at.isoformat() if r.notified_at else None,
            "receipt_printed_at": r.receipt_printed_at.isoformat() if r.receipt_printed_at else None,
        }
        for r in rows
    ]


def mark_settlement_transferred(db: Session, settlement_id: int) -> Optional[StoreSettlement]:
    """บันทึกว่าโอนเงินให้ร้านแล้ว"""
    st = db.query(StoreSettlement).filter(StoreSettlement.id == settlement_id).first()
    if not st:
        return None
    st.status = "transferred"
    st.transferred_at = datetime.utcnow()
    db.commit()
    db.refresh(st)
    return st


def notify_store_settlement(db: Session, settlement_id: int) -> Optional[StoreSettlement]:
    """แจ้งร้านว่าเงินเข้าเรียบร้อยแล้ว (ร้านสามารถพิมพ์ใบเสร็จรับเงินมอบลูกค้าได้)"""
    st = db.query(StoreSettlement).filter(StoreSettlement.id == settlement_id).first()
    if not st:
        return None
    st.status = "notified"
    st.notified_at = datetime.utcnow()
    db.commit()
    db.refresh(st)
    return st


def get_store_settlements_for_receipt(
    db: Session,
    store_id: int,
    notified_only: bool = True,
) -> List[dict]:
    """รายการที่ร้านสามารถพิมพ์ใบเสร็จรับเงินได้ (เงินเข้าเรียบร้อยแล้ว)"""
    q = (
        db.query(StoreSettlement)
        .filter(StoreSettlement.store_id == store_id)
        .order_by(StoreSettlement.settlement_date.desc())
    )
    if notified_only:
        q = q.filter(StoreSettlement.status == "notified")
    rows = q.limit(100).all()
    return [
        {
            "id": r.id,
            "settlement_date": r.settlement_date.isoformat() if r.settlement_date else None,
            "amount": r.amount,
            "status": r.status,
            "notified_at": r.notified_at.isoformat() if r.notified_at else None,
        }
        for r in rows
    ]
