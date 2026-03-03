"""
Audit Log Service - บันทึกทุกการดำเนินการในระบบเพื่อใช้เป็นหลักฐานอ้างอิง
"""
import json
import logging
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models import AuditLog

logger = logging.getLogger(__name__)


def _serialize(val: Any) -> Optional[str]:
    if val is None:
        return None
    try:
        return json.dumps(val, ensure_ascii=False) if not isinstance(val, str) else val
    except Exception:
        return str(val)


def write_audit_log(
    db: Session,
    action: str,
    table_name: str,
    record_id: Optional[int] = None,
    old_values: Any = None,
    new_values: Any = None,
    user_id: Optional[int] = None,
    source: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> AuditLog:
    """
    บันทึก audit log ทุกการดำเนินการ
    source: 'admin' | 'store_pos' | 'member' | 'system'
    """
    entry = AuditLog(
        user_id=user_id,
        source=source or "system",
        action=action,
        table_name=table_name,
        record_id=record_id,
        old_values=_serialize(old_values),
        new_values=_serialize(new_values),
        ip_address=ip_address,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    logger.debug("Audit log: %s %s id=%s", action, table_name, record_id)
    return entry
