"""
Signage API - จอที่ 2 สำหรับ POS (แสดง QR Payment + Digital Signage)
เมื่อ store-pos กดสร้าง QR จะส่งมาที่ set-display, จอ signage แสดง QR
เมื่อจ่ายเงินแล้ว webhook จะ set status=paid, signage แสดง "ได้รับเงินเรียบร้อยแล้ว" + พูด แล้วเล่น signage ต่อ
"""
from typing import Optional, Dict, Any
from fastapi import APIRouter, Query
from pydantic import BaseModel

# In-memory state ต่อร้าน: store_id -> { qr_image, amount, status, updated_at }
_signage_state: Dict[int, Dict[str, Any]] = {}


def set_signage_display(store_id: int, qr_image: str, amount: float) -> None:
    """ให้ store-pos เรียกเมื่อกดสร้าง PromptPay QR"""
    _signage_state[store_id] = {
        "qr_image": qr_image,
        "amount": amount,
        "status": "waiting_payment",
    }


def set_signage_paid(store_id: int) -> None:
    """ให้ webhook เรียกเมื่อรับเงินแล้ว (ref1 -> store_id)"""
    if store_id in _signage_state:
        _signage_state[store_id]["status"] = "paid"


def get_signage_display(store_id: int) -> Optional[Dict[str, Any]]:
    """ให้จอ signage poll"""
    return _signage_state.get(store_id)


def ack_signage_paid(store_id: int) -> None:
    """ให้จอ signage เรียกหลังแสดง "ได้รับเงินเรียบร้อยแล้ว" แล้ว เพื่อกลับไปโหมด signage"""
    if store_id in _signage_state:
        _signage_state[store_id]["status"] = "acked"
        # เคลียร์เพื่อกลับไปโหมด idle (หรือเก็บไว้แสดง signage)
        del _signage_state[store_id]


def clear_signage_display(store_id: int) -> None:
    """ให้ store-pos เรียกเมื่อกดยกเลิก การจ่าย เพื่อให้จอ signage กลับไปโหมด default"""
    if store_id in _signage_state:
        del _signage_state[store_id]


router = APIRouter(prefix="/api/signage", tags=["signage"])


class SetDisplayPayload(BaseModel):
    store_id: int
    qr_image: str  # base64 data URI
    amount: float


@router.post("/set-display")
async def post_set_display(payload: SetDisplayPayload):
    """Store-pos เรียกเมื่อกดสร้าง PromptPay QR Code เพื่อให้จอที่ 2 แสดง QR ทันที"""
    set_signage_display(payload.store_id, payload.qr_image, payload.amount)
    return {"ok": True, "store_id": payload.store_id}


@router.get("/display")
async def get_display(store_id: int = Query(..., description="รหัสร้าน")):
    """จอ signage poll เพื่อดึงสถานะปัจจุบัน (qr_image, amount, status)"""
    data = get_signage_display(store_id)
    if not data:
        return {"status": None, "qr_image": None, "amount": None}
    return {
        "status": data.get("status"),
        "qr_image": data.get("qr_image"),
        "amount": data.get("amount"),
    }


@router.post("/ack-paid")
async def post_ack_paid(store_id: int = Query(..., description="รหัสร้าน")):
    """จอ signage เรียกหลังแสดง 'ได้รับเงินเรียบร้อยแล้ว' และพูดแล้ว เพื่อกลับไปเล่น signage ต่อ"""
    ack_signage_paid(store_id)
    return {"ok": True}


@router.post("/clear")
async def post_clear(store_id: int = Query(..., description="รหัสร้าน")):
    """Store-pos เรียกเมื่อกดยกเลิก การจ่าย เพื่อล้างจอ signage กลับไปโหมด default"""
    clear_signage_display(store_id)
    return {"ok": True, "store_id": store_id}
