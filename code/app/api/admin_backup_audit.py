"""
Admin/Store POS: รายการสำรองฉุกเฉิน (กรณีไฟดับ) และ Audit Logs
- สร้างรายการ backup: ได้ทั้งจาก admin และ store_pos (ต้องล็อกอิน)
- ดูย้อนหลังรายการ backup: เฉพาะ admin
- ดู audit logs: เฉพาะ admin
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models import EmergencyBackupEntry, AuditLog, User, Store
from app.api.auth import get_current_session_user, require_admin
from app.services.audit_log import write_audit_log

router = APIRouter(prefix="/api", tags=["admin-backup-audit"])


class EmergencyBackupCreate(BaseModel):
    source: str  # 'admin' | 'store_pos'
    store_id: Optional[int] = None
    entry_type: str  # sale, exchange, topup, other
    amount: float
    description: Optional[str] = None


@router.post("/emergency-backup")
def create_emergency_backup(
    body: EmergencyBackupCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_session_user),
):
    """กรอกข้อมูลรายการสำรอง (กรณีไฟดับ/ระบบล่ม) - ต้องล็อกอิน"""
    if body.source not in ("admin", "store_pos"):
        raise HTTPException(status_code=400, detail="source ต้องเป็น admin หรือ store_pos")
    if body.entry_type not in ("sale", "exchange", "topup", "other"):
        raise HTTPException(status_code=400, detail="entry_type ต้องเป็น sale, exchange, topup หรือ other")
    if body.amount < 0:
        raise HTTPException(status_code=400, detail="amount ต้องไม่ต่ำกว่า 0")
    user_id = user["user_id"]
    if body.source == "store_pos" and body.store_id and user.get("store_ids"):
        if body.store_id not in user["store_ids"]:
            raise HTTPException(status_code=403, detail="ไม่มีสิทธิ์ร้านนี้")
    entry = EmergencyBackupEntry(
        source=body.source,
        store_id=body.store_id,
        entry_type=body.entry_type,
        amount=body.amount,
        description=body.description or "",
        entered_by_user_id=user_id,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    ip = request.client.host if request.client else None
    write_audit_log(
        db, action="emergency_backup_create", table_name="emergency_backup_entries",
        record_id=entry.id, new_values={"amount": body.amount, "entry_type": body.entry_type},
        user_id=user_id, source=body.source, ip_address=ip,
    )
    return {"id": entry.id, "created_at": entry.created_at.isoformat() if entry.created_at else None}


@router.get("/emergency-backup")
def list_emergency_backup(
    source: Optional[str] = Query(None),
    store_id: Optional[int] = Query(None),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
    user: dict = Depends(require_admin),
):
    """ดูย้อนหลังรายการสำรอง - เฉพาะ admin"""
    q = db.query(EmergencyBackupEntry).order_by(EmergencyBackupEntry.id.desc()).limit(limit)
    if source:
        q = q.filter(EmergencyBackupEntry.source == source)
    if store_id is not None:
        q = q.filter(EmergencyBackupEntry.store_id == store_id)
    rows = q.all()
    out = []
    for r in rows:
        out.append({
            "id": r.id,
            "source": r.source,
            "store_id": r.store_id,
            "entry_type": r.entry_type,
            "amount": r.amount,
            "description": r.description,
            "entered_by_user_id": r.entered_by_user_id,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })
    return {"items": out}


@router.get("/audit-logs")
def list_audit_logs(
    source: Optional[str] = Query(None),
    table_name: Optional[str] = Query(None),
    limit: int = Query(200, le=1000),
    db: Session = Depends(get_db),
    user: dict = Depends(require_admin),
):
    """ดู audit logs - เฉพาะ admin"""
    q = db.query(AuditLog).order_by(AuditLog.id.desc()).limit(limit)
    if source:
        q = q.filter(AuditLog.source == source)
    if table_name:
        q = q.filter(AuditLog.table_name == table_name)
    rows = q.all()
    return {
        "items": [
            {
                "id": r.id,
                "user_id": r.user_id,
                "source": r.source,
                "action": r.action,
                "table_name": r.table_name,
                "record_id": r.record_id,
                "old_values": r.old_values,
                "new_values": r.new_values,
                "ip_address": r.ip_address,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]
    }
