"""
Signage API - จอที่ 2 สำหรับ POS (แสดง QR Payment + Digital Signage)
เมื่อ store-pos กดสร้าง QR จะส่งมาที่ set-display, จอ signage แสดง QR
เมื่อจ่ายเงินแล้ว webhook จะ set status=paid, signage แสดง "ได้รับเงินเรียบร้อยแล้ว" + พูด แล้วเล่น signage ต่อ
เมื่อ idle (ไม่มี QR): แสดง video/โฆษณา loop
"""
import json
from pathlib import Path
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, Query, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Store

_SIGNAGE_MEDIA_FILE = Path(__file__).resolve().parent.parent / "data" / "signage_media.json"

DEFAULT_SIGNAGE_MEDIA = [
    {"type": "image", "url": "https://picsum.photos/1200/800?random=1", "duration": 2},
    {"type": "image", "url": "https://picsum.photos/1200/800?random=2", "duration": 2},
    {"type": "image", "url": "https://picsum.photos/1200/800?random=3", "duration": 2},
]

# In-memory state ต่อร้าน: store_id -> { qr_image, amount, status, order_items, ... }
_signage_state: Dict[int, Dict[str, Any]] = {}


def set_signage_display(
    store_id: int,
    qr_image: Optional[str] = None,
    amount: float = 0,
    order_items: Optional[List[dict]] = None,
    qr_plain_text: Optional[str] = None,
) -> None:
    """ให้ store-pos เรียกเมื่อกดสร้าง PromptPay QR (qr_image = data URL หรือ qr_plain_text = ข้อความ Stripe)"""
    _signage_state[store_id] = {
        "qr_image": qr_image or None,
        "qr_plain_text": qr_plain_text or None,
        "amount": amount,
        "status": "waiting_payment",
        "order_items": order_items or [],
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


def set_signage_cart(store_id: int, order_items: List[dict], amount: float) -> None:
    """ให้ store-pos เรียกเมื่อเพิ่ม/ลด/แก้ไขรายการในตะกร้า (ยังไม่กด PromptPay) – จอที่ 2 แสดงรายการเท่านั้น ไม่แสดง QR
    ถ้าตอนนี้จอแสดง QR รอชำระ (waiting_payment) จะไม่เขียนทับ เพื่อไม่ให้ Stripe QR หาย"""
    if not order_items:
        if store_id in _signage_state and _signage_state[store_id].get("status") == "cart":
            del _signage_state[store_id]
        return
    # ไม่เขียนทับเมื่อกำลังแสดง QR รอชำระ (กด PromptPay แล้ว) – ให้จอ signage คงแสดง QR ไว้
    if store_id in _signage_state and _signage_state[store_id].get("status") == "waiting_payment":
        return
    _signage_state[store_id] = {
        "status": "cart",
        "order_items": order_items,
        "amount": amount,
        "qr_image": None,
    }


router = APIRouter(prefix="/api/signage", tags=["signage"])


class SetDisplayPayload(BaseModel):
    store_id: int
    qr_image: Optional[str] = None  # data URL (EMV/legacy)
    qr_plain_text: Optional[str] = None  # ข้อความ Stripe PromptPay สำหรับสร้าง QR ที่ signage
    amount: float = 0
    order_items: Optional[List[dict]] = None  # [{ name, qty, line_total }]


class SetCartPayload(BaseModel):
    store_id: int
    order_items: List[dict]  # [{ name, qty, unit_price?, line_total? }]
    amount: float


@router.post("/set-cart")
async def post_set_cart(payload: SetCartPayload):
    """Store-pos เรียกเมื่อเพิ่ม/ลด/ล้างรายการ – จอที่ 2 แสดงรายการสินค้าพร้อมกัน (ไม่แสดง QR จนกว่าจะกด PromptPay/พิมพ์ Order+QR)"""
    set_signage_cart(payload.store_id, payload.order_items or [], payload.amount)
    return {"ok": True, "store_id": payload.store_id}


@router.post("/set-display")
async def post_set_display(payload: SetDisplayPayload):
    """Store-pos เรียกเมื่อกดสร้าง PromptPay QR (ส่ง qr_image หรือ qr_plain_text สำหรับ Stripe)"""
    set_signage_display(
        payload.store_id,
        qr_image=payload.qr_image,
        amount=payload.amount,
        order_items=payload.order_items,
        qr_plain_text=payload.qr_plain_text,
    )
    return {"ok": True, "store_id": payload.store_id}


@router.get("/display")
async def get_display(store_id: int = Query(..., description="รหัสร้าน"), db: Session = Depends(get_db)):
    """จอ signage poll เพื่อดึงสถานะปัจจุบัน (qr_image, amount, status, store_name, order_items)"""
    data = get_signage_display(store_id)
    store_name = ""
    try:
        store = db.query(Store).filter(Store.id == store_id).first()
        if store:
            store_name = store.name or ""
    except Exception:
        pass

    if not data:
        return {"status": None, "qr_image": None, "qr_plain_text": None, "amount": None, "store_name": store_name, "order_items": []}
    return {
        "status": data.get("status"),
        "qr_image": data.get("qr_image"),
        "qr_plain_text": data.get("qr_plain_text"),
        "amount": data.get("amount"),
        "store_name": store_name,
        "order_items": data.get("order_items") or [],
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


def _load_signage_media() -> List[dict]:
    """โหลดรายการ video/โฆษณาสำหรับ idle mode"""
    if _SIGNAGE_MEDIA_FILE.exists():
        try:
            with open(_SIGNAGE_MEDIA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    return data
        except Exception:
            pass
    return DEFAULT_SIGNAGE_MEDIA


@router.get("/media")
async def get_signage_media():
    """ดึงรายการ video/โฆษณาสำหรับ idle mode (แก้ไขได้ที่ data/signage_media.json)"""
    return {"items": _load_signage_media()}
