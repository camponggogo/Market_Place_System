"""
Payment Callback API - รับ Back Transaction จากธนาคาร, รายงาน, รายการโอนสิ้นวัน, แจ้งร้าน
อ้างอิง:
- SCB Developers: https://developer.scb/ - QR Payment (แจ้งร้านเมื่อชำระเสร็จ), Slip Verification
- K Bank (ธนาคารกสิกร) K API: https://apiportal.kasikornbank.com - QR Payment Webhook
- มาตรฐาน Thai QR Payment: reference1/2/3, totalAmount, transactionId, transactionDate
"""
import logging
from datetime import datetime, date
from typing import Optional, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import BACKEND_URL, OMISE_PUBLIC_KEY, OMISE_SECRET_KEY, STRIPE_WEBHOOK_SECRET
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
from app.api.admin import resolve_banking_profile_for_store
from app.services import scb_deeplink
from app.models import Store, Order, Customer, CustomerBalance, MemberActivity, ECoupon
from app.services import omise_promptpay, stripe_promptpay
import hashlib
import secrets
import string
import hmac as hmacc
import json

logger = logging.getLogger(__name__)
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


class KBankQRPaymentPayload(BaseModel):
    """
    Payload รูปแบบ K Bank (K API Portal) / มาตรฐาน Thai QR Payment
    รองรับฟิลด์ที่ apiportal.kasikornbank.com และธนาคารไทยใช้ (reference1, totalAmount ฯลฯ)
    """
    # อ้างอิงใน QR (ref1 = store token, ref2, ref3) - รับได้ทั้ง reference1 และ ref1
    reference1: Optional[str] = None
    ref1: Optional[str] = None
    reference2: Optional[str] = None
    ref2: Optional[str] = None
    reference3: Optional[str] = None
    ref3: Optional[str] = None
    # จำนวนเงิน (บาท)
    totalAmount: Optional[float] = None
    amount: Optional[float] = None
    # เลขที่อ้างอิงธุรกรรม
    transactionId: Optional[str] = None
    transRef: Optional[str] = None
    slipReference: Optional[str] = None
    # เวลาชำระ (ISO 8601 หรือ timestamp มิลลิวินาที)
    transactionDate: Optional[str] = None
    paidAt: Optional[str] = None
    dateTime: Optional[str] = None
    currencyCode: Optional[str] = None
    bankAccount: Optional[str] = None

    class Config:
        extra = "ignore"


def _kbank_payload_to_back_transaction(body: dict) -> BackTransactionPayload:
    """แมป payload จาก K Bank / Thai QR Payment เป็น BackTransactionPayload"""
    ref1 = (body.get("reference1") or body.get("ref1") or "").strip()
    ref2 = body.get("reference2") or body.get("ref2")
    ref3 = body.get("reference3") or body.get("ref3")
    amount = body.get("totalAmount") or body.get("amount")
    slip = body.get("transactionId") or body.get("transRef") or body.get("slipReference")
    paid_at = body.get("transactionDate") or body.get("paidAt") or body.get("dateTime")
    bank_account = body.get("bankAccount") or body.get("bank_account")
    if not ref1:
        raise ValueError("reference1 หรือ ref1 จำเป็น")
    if amount is None:
        raise ValueError("totalAmount หรือ amount จำเป็น")
    return BackTransactionPayload(
        ref1=ref1,
        ref2=str(ref2).strip() if ref2 else None,
        ref3=str(ref3).strip() if ref3 else None,
        amount=float(amount),
        paid_at=paid_at,
        slip_reference=str(slip).strip() if slip else None,
        bank_account=str(bank_account).strip() if bank_account else None,
        raw_payload=body,
    )


class SettlementNotifyRequest(BaseModel):
    settlement_id: int


class CreateGatewayQRRequest(BaseModel):
    amount: float  # บาท
    order_id: Optional[int] = None  # ถ้ามี ส่ง ref2 ใน metadata ให้ webhook อัปเดต Order
    order_lines: Optional[list] = None  # ถ้ามีและไม่มี order_id จะสร้าง Order แล้วใช้เป็น ref2


class CreateChargeCardRequest(BaseModel):
    amount: float  # บาท
    token: str  # Omise card token จาก Omise.js
    order_id: Optional[int] = None


# --- Endpoints ---

def _resolve_omise_keys(db: Session, store: Store) -> tuple:
    """คืน (public_key, secret_key) – จาก BankingProfile ก่อน ถ้าไม่มีใช้ config.ini"""
    profile = resolve_banking_profile_for_store(db, store)
    if profile and getattr(profile, "provider_type", None) == "omise":
        pk = getattr(profile, "omise_public_key", None) or ""
        sk = getattr(profile, "omise_secret_key", None) or ""
        if pk and sk:
            return (pk, sk)
    if OMISE_PUBLIC_KEY and OMISE_SECRET_KEY:
        return (OMISE_PUBLIC_KEY, OMISE_SECRET_KEY)
    return ("", "")


def _resolve_scb_config(db: Session, store: Store) -> tuple:
    """คืน (api_key, api_secret, callback_url) – จาก BankingProfile scb_deeplink หรือ Store"""
    profile = resolve_banking_profile_for_store(db, store)
    if profile and getattr(profile, "provider_type", None) == "scb_deeplink":
        ak = getattr(profile, "scb_api_key", None) or ""
        asec = getattr(profile, "scb_api_secret", None) or ""
        cb = getattr(profile, "scb_callback_url", None) or ""
        if ak and asec:
            return (ak, asec, cb or f"{BACKEND_URL.rstrip('/')}/api/payment-callback/webhook")
    if getattr(store, "scb_api_key", None) and getattr(store, "scb_api_secret", None):
        cb = getattr(store, "scb_callback_url", None) or ""
        return (
            store.scb_api_key,
            store.scb_api_secret,
            cb or f"{BACKEND_URL.rstrip('/')}/api/payment-callback/webhook",
        )
    return ("", "", "")


@router.get("/stores/{store_id}/gateway-info")
async def get_gateway_info(store_id: int, db: Session = Depends(get_db)):
    """
    คืนค่า payment gateway ของร้าน (สำหรับ Store POS เลือกใช้ Omise / SCB / QR ธรรมดา)
    - omise: ใช้ Omise API (ลำดับแรก)
    - scb_deeplink: ใช้ SCB Partners API (PromptPay ผ่าน SCB Easy)
    """
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    profile = resolve_banking_profile_for_store(db, store)
    provider = getattr(profile, "provider_type", None) if profile else None
    # ชี้ไป Omise ก่อน ถ้ามีการตั้งค่า (config.ini หรือ Banking Profile)
    pk, _ = _resolve_omise_keys(db, store)
    if pk:
        return {"provider": "omise", "omise_public_key": pk}
    ak, _, _ = _resolve_scb_config(db, store)
    if ak:
        return {"provider": "scb_deeplink"}
    if provider:
        out = {"provider": provider}
        if provider == "omise":
            out["omise_public_key"] = getattr(profile, "omise_public_key", None) or ""
        return out
    return {"provider": None}


@router.post("/stores/{store_id}/create-gateway-qr")
async def create_gateway_qr(
    store_id: int,
    body: CreateGatewayQRRequest,
    db: Session = Depends(get_db),
):
    """
    สร้าง QR ชำระผ่าน Gateway ที่ตั้งไว้ให้ร้าน (Omise / Stripe)
    ถ้า profile เป็น omise หรือ stripe จะสร้าง charge/payment_intent และคืน QR หรือ client_secret
    metadata.ref1 = store.token เพื่อให้ webhook แมปกับร้านได้
    """
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    profile = resolve_banking_profile_for_store(db, store)
    has_scb_store = getattr(store, "scb_api_key", None) and getattr(store, "scb_api_secret", None)
    if not profile and not has_scb_store:
        raise HTTPException(status_code=400, detail="No payment gateway profile for this store")
    ref1 = getattr(store, "token", None) or ""
    if not ref1:
        raise HTTPException(status_code=400, detail="Store has no token")
    amount_satang = int(round(body.amount * 100))
    if amount_satang < 1:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    order_id_for_ref2 = body.order_id
    if order_id_for_ref2 is None and body.order_lines:
        order = Order(
            store_id=store_id,
            total_amount=body.amount,
            status="pending",
            items=json.dumps(body.order_lines, ensure_ascii=False),
        )
        db.add(order)
        db.commit()
        db.refresh(order)
        order_id_for_ref2 = order.id
    metadata = {"ref1": ref1, "store_id": str(store_id)}
    if order_id_for_ref2 is not None:
        metadata["ref2"] = str(order_id_for_ref2)

    provider = getattr(profile, "provider_type", None)
    if provider == "omise":
        sk = getattr(profile, "omise_secret_key", None)
        if not sk:
            raise HTTPException(status_code=400, detail="Omise secret key not configured")
        try:
            charge = omise_promptpay.create_charge_promptpay(
                secret_key=sk,
                amount_satang=amount_satang,
                metadata=metadata,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        qr_uri = charge.get("_qr_download_uri")
        qr_base64 = None
        if qr_uri:
            import httpx
            try:
                r = httpx.get(qr_uri, timeout=10.0)
                if r.status_code == 200:
                    import base64
                    qr_base64 = "data:image/svg+xml;base64," + base64.b64encode(r.content).decode()
            except Exception:
                pass
        return {
            "provider": "omise",
            "charge_id": charge.get("id"),
            "order_id": order_id_for_ref2,
            "amount": body.amount,
            "qr_image": qr_base64,
            "status": charge.get("status"),
        }
    if provider == "stripe":
        sk = getattr(profile, "stripe_secret_key", None)
        if not sk:
            raise HTTPException(status_code=400, detail="Stripe secret key not configured")
        try:
            pi = stripe_promptpay.create_payment_intent_promptpay(
                secret_key=sk,
                amount_satang=amount_satang,
                metadata={"ref1": ref1, "store_id": str(store_id)},
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return {
            "provider": "stripe",
            "payment_intent_id": pi.get("id"),
            "client_secret": pi.get("client_secret"),
            "amount": body.amount,
            "status": pi.get("status"),
        }
    if provider == "apple_pay":
        sk = getattr(profile, "stripe_secret_key", None)
        if not sk:
            raise HTTPException(status_code=400, detail="Apple Pay ใช้ Stripe – กรุณาตั้ง Stripe Secret Key")
        try:
            pi = stripe_promptpay.create_payment_intent_apple_pay(
                secret_key=sk,
                amount_satang=amount_satang,
                metadata={"ref1": ref1, "store_id": str(store_id)},
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return {
            "provider": "apple_pay",
            "payment_intent_id": pi.get("id"),
            "client_secret": pi.get("client_secret"),
            "amount": body.amount,
            "status": pi.get("status"),
        }
    if provider == "scb_deeplink" or (not profile and getattr(store, "scb_api_key", None)):
        ak, asec, callback_url = _resolve_scb_config(db, store)
        if not ak or not asec:
            raise HTTPException(status_code=400, detail="SCB API Key/Secret ไม่ได้ตั้งค่า (Store หรือ Banking Profile)")
        bid = getattr(store, "biller_id", None) or getattr(store, "tax_id", None)
        biller_id = None
        if bid:
            b = "".join(c for c in str(bid) if c.isdigit())
            if b:
                biller_id = (b + "99" if len(b) <= 13 else b)[:15].zfill(15)
        try:
            access_token = scb_deeplink.get_oauth_token(api_key=ak, api_secret=asec)
            result = scb_deeplink.create_deeplink_transaction(
                access_token=access_token,
                api_key=ak,
                payment_amount=body.amount,
                ref1=ref1,
                ref2=str(order_id_for_ref2) if order_id_for_ref2 else None,
                account_to=biller_id or None,
                callback_url=callback_url or f"{BACKEND_URL.rstrip('/')}/api/payment-callback/webhook",
                merchant_name=getattr(store, "name", None) or "Store",
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        data = result.get("data") or result
        qr_image = data.get("qrCode") or data.get("qr_code")
        deeplink_url = data.get("deeplinkUrl") or data.get("deeplink_url")
        if not qr_image and deeplink_url:
            import qrcode
            import base64
            buf = qrcode.make(deeplink_url)
            import io
            bio = io.BytesIO()
            buf.save(bio, format="PNG")
            qr_image = "data:image/png;base64," + base64.b64encode(bio.getvalue()).decode()
        return {
            "provider": "scb_deeplink",
            "order_id": order_id_for_ref2,
            "amount": body.amount,
            "qr_image": qr_image,
            "deeplink_url": deeplink_url,
            "status": "pending",
        }
    raise HTTPException(
        status_code=400,
        detail=f"Gateway {provider or 'default'} use existing /api/stores/{{id}}/generate-promptpay-qr for K Bank",
    )


@router.post("/stores/{store_id}/charge-card")
async def create_charge_card(
    store_id: int,
    body: CreateChargeCardRequest,
    db: Session = Depends(get_db),
):
    """
    สร้าง Omise Charge แบบบัตร (Credit/Debit) สำหรับ Store POS
    token จาก Omise.js (เก็บบัตรแล้วได้ token)
    """
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    pk, sk = _resolve_omise_keys(db, store)
    if not sk:
        raise HTTPException(status_code=400, detail="Omise secret key not configured (ตั้งค่าที่ config.ini หรือ Banking Profile)")
    ref1 = getattr(store, "token", None) or ""
    amount_satang = int(round(body.amount * 100))
    if amount_satang < 2000:
        raise HTTPException(status_code=400, detail="Omise card minimum 20 THB")
    metadata = {"ref1": ref1, "store_id": str(store_id)}
    if body.order_id is not None:
        metadata["ref2"] = str(body.order_id)
    try:
        charge = omise_promptpay.create_charge_card(
            secret_key=sk,
            amount_satang=amount_satang,
            card_token=body.token,
            metadata=metadata,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "charge_id": charge.get("id"),
        "status": charge.get("status"),
        "amount": body.amount,
        "authorizer_uri": charge.get("authorize_uri"),
    }


@router.get("/stores/{store_id}/charge-status/{charge_id}")
async def get_charge_status(
    store_id: int,
    charge_id: str,
    db: Session = Depends(get_db),
):
    """ดึงสถานะ charge จาก Omise (สำหรับ poll หลังสร้าง charge บัตร/QR)"""
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    pk, sk = _resolve_omise_keys(db, store)
    if not sk:
        raise HTTPException(status_code=400, detail="Omise secret key not configured")
    try:
        charge = omise_promptpay.get_charge(secret_key=sk, charge_id=charge_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    amount_satang = int(charge.get("amount") or 0)
    return {
        "charge_id": charge.get("id"),
        "status": charge.get("status"),
        "amount": amount_satang / 100.0,
        "paid": charge.get("paid", False),
    }


@router.get("/webhook/links")
async def webhook_links():
    """
    คืนค่า URL สำหรับลงทะเบียน Webhook แยกตามผู้ให้บริการ
    """
    base = (BACKEND_URL or "").rstrip("/")
    stripe_url = f"{base}/api/payment-callback/webhook/stripe"
    return {
        "scb": f"{base}/api/payment-callback/webhook",
        "kbank": f"{base}/api/payment-callback/webhook/kbank",
        "omise": f"{base}/api/payment-callback/webhook/omise",
        "stripe": stripe_url,
        "apple_pay": stripe_url,
    }


@router.get("/webhook")
async def webhook_health():
    """
    ให้ธนาคาร/ระบบภายนอกตรวจสอบว่า Webhook endpoint ยังทำงาน (health check)
    ใช้ตอนลงทะเบียน Webhook URL กับ SCB เท่านั้น (ไม่ใช้กับ K Bank)
    """
    return {"status": "ok", "message": "SCB webhook endpoint is ready", "provider": "scb"}


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
        logger.info("Bank callback received: ref1=%s amount=%.2f", payload.ref1[:20] + "..." if len(payload.ref1) > 20 else payload.ref1, payload.amount)
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
        logger.info("Back transaction saved: id=%s store_id=%s ref1=%s amount=%.2f", back.id, back.store_id, back.ref1, back.amount)
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
    logger.info("SCB webhook POST received: ref1=%s amount=%.2f", payload.ref1[:20] + "..." if len(payload.ref1) > 20 else payload.ref1, payload.amount)
    return await post_back_transaction(payload=payload, db=db)


@router.get("/webhook/kbank")
async def webhook_kbank_health():
    """
    Health check สำหรับ K Bank (ธนาคารกสิกร) QR Payment Webhook
    ลงทะเบียน URL: https://your-domain.com/api/payment-callback/webhook/kbank
    """
    return {"status": "ok", "message": "K Bank QR Payment webhook is ready", "provider": "kbank"}


@router.post("/webhook/kbank")
async def webhook_kbank_receive(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Webhook สำหรับ K Bank (ธนาคารกสิกร) QR Payment จาก K API Portal
    รองรับ payload มาตรฐาน Thai QR Payment: reference1, reference2, reference3,
    totalAmount, transactionId, transactionDate ฯลฯ
    ดูเอกสาร: https://apiportal.kasikornbank.com/app/exercises/0e53e69a-d024-49b6-b655-8fbbfc9d5cb6/20
    """
    try:
        body = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Body must be a JSON object")
    try:
        payload = _kbank_payload_to_back_transaction(body)
    except ValueError as e:
        logger.warning("K Bank webhook invalid payload: %s", e)
        raise HTTPException(status_code=400, detail=str(e))
    ref1 = (payload.ref1 or "")[:20] + ("..." if len(payload.ref1 or "") > 20 else "")
    logger.info("K Bank webhook POST received: ref1=%s amount=%.2f", ref1, payload.amount)
    return await post_back_transaction(payload=payload, db=db)


@router.get("/webhook/omise")
async def webhook_omise_health():
    """Health check สำหรับ Omise Webhook (ลงทะเบียนที่ dashboard.omise.co)"""
    return {"status": "ok", "message": "Omise webhook is ready", "provider": "omise"}


@router.post("/webhook/omise")
async def webhook_omise_receive(request: Request, db: Session = Depends(get_db)):
    """
    Webhook จาก Omise (charge.complete)
    ต้องส่ง metadata.ref1 (store token 20 หลัก) ตอนสร้าง charge เพื่อแมปกับร้าน
    อ้างอิง: https://docs.omise.co/api-webhooks
    """
    try:
        body = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Body must be a JSON object")
    key = body.get("key")
    if key != "charge.complete":
        return {"received": True}
    data = body.get("data") or {}
    charge = data if isinstance(data, dict) and data.get("object") == "charge" else data.get("charge") or data
    if not charge or charge.get("status") != "successful":
        return {"received": True}
    meta = charge.get("metadata") or {}
    ref1 = meta.get("ref1") or ""
    ref2 = meta.get("ref2")
    ref3 = meta.get("ref3")
    amount_satang = int(charge.get("amount") or 0)
    amount_baht = amount_satang / 100.0
    if not ref1:
        logger.warning("Omise webhook: charge %s has no metadata.ref1", charge.get("id"))
        return {"received": True}
    logger.info("Omise webhook: charge.complete ref1=%s amount=%.2f ref2=%s", ref1[:20], amount_baht, ref2)
    payload = BackTransactionPayload(ref1=ref1, amount=amount_baht, ref2=ref2, ref3=ref3, raw_payload=body)
    return await post_back_transaction(payload=payload, db=db)


@router.get("/webhook/stripe")
async def webhook_stripe_health():
    """Health check สำหรับ Stripe Webhook (ลงทะเบียนที่ dashboard.stripe.com)"""
    return {"status": "ok", "message": "Stripe webhook is ready", "provider": "stripe"}


def _verify_stripe_signature(payload_body: bytes, sig_header: str, secret: str) -> bool:
    """Verify Stripe-Signature (v1 = HMAC-SHA256 of timestamp.payload)."""
    if not sig_header or not secret:
        return True
    parts = {}
    for p in sig_header.split(","):
        if "=" in p:
            k, v = p.strip().split("=", 1)
            parts[k.strip()] = v.strip()
    t = parts.get("t") or ""
    v1 = parts.get("v1") or ""
    if not t or not v1:
        return False
    msg = f"{t}.{payload_body.decode('utf-8', errors='replace')}"
    expected = hmacc.new(secret.encode("utf-8"), msg.encode("utf-8"), hashlib.sha256).hexdigest()
    return hmacc.compare_digest(expected, v1)


@router.post("/webhook/stripe")
async def webhook_stripe_receive(request: Request, db: Session = Depends(get_db)):
    """
    Webhook จาก Stripe (payment_intent.succeeded)
    ต้องส่ง metadata.ref1 (store token) ตอนสร้าง PaymentIntent
    ถ้ามี STRIPE_WEBHOOK_SECRET จะตรวจสอบลายเซ็น (ใช้กับ ngrok / production)
    อ้างอิง: https://docs.stripe.com/webhooks
    """
    payload_body = await request.body()
    sig_header = request.headers.get("Stripe-Signature") or ""
    if STRIPE_WEBHOOK_SECRET and not _verify_stripe_signature(payload_body, sig_header, STRIPE_WEBHOOK_SECRET):
        logger.warning("Stripe webhook: invalid signature")
        raise HTTPException(status_code=400, detail="Invalid Stripe signature")
    try:
        body = json.loads(payload_body)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Body must be a JSON object")
    ev_type = body.get("type")
    if ev_type != "payment_intent.succeeded":
        return {"received": True}
    data = body.get("data", {}).get("object") or {}
    meta = data.get("metadata") or {}
    ref1 = meta.get("ref1") or ""
    customer_id_raw = meta.get("customer_id")
    intent_type = meta.get("type") or ""
    amount_satang = int(data.get("amount") or 0)
    amount_baht = amount_satang / 100.0

    # Member: เติมเงิน (member_topup) หรือซื้อ E-Coupon (member_ecoupon)
    if customer_id_raw and intent_type in ("member_topup", "member_ecoupon"):
        try:
            customer_id = int(customer_id_raw)
        except (ValueError, TypeError):
            customer_id = None
        if customer_id:
            customer = db.query(Customer).filter(Customer.id == customer_id).first()
            if customer:
                if intent_type == "member_topup":
                    bal = db.query(CustomerBalance).filter(CustomerBalance.customer_id == customer_id).first()
                    if not bal:
                        bal = CustomerBalance(customer_id=customer_id, balance=0.0)
                        db.add(bal)
                    bal.balance = (bal.balance or 0) + amount_baht
                    db.add(bal)
                    act = MemberActivity(
                        customer_id=customer_id,
                        activity_type="topup",
                        amount=amount_baht,
                        description=f"เติมเงินผ่าน Stripe {amount_baht:.2f} บาท",
                    )
                    db.add(act)
                    db.commit()
                    logger.info("Stripe webhook: member_topup customer_id=%s +%.2f balance=%.2f", customer_id, amount_baht, bal.balance)
                else:  # member_ecoupon
                    def _gen_ecode(prefix="EC", length=10):
                        return prefix + "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(length))
                    code = _gen_ecode()
                    while db.query(ECoupon).filter(ECoupon.code == code).first():
                        code = _gen_ecode()
                    paid_at = datetime.utcnow()
                    ec = ECoupon(
                        code=code,
                        amount=amount_baht,
                        customer_id=customer_id,
                        status="assigned",
                        payment_method="stripe",
                        paid_at=paid_at,
                    )
                    db.add(ec)
                    act = MemberActivity(
                        customer_id=customer_id,
                        activity_type="redeem",
                        amount=amount_baht,
                        description=f"ซื้อ E-Coupon {amount_baht:.2f} บาท (Stripe)",
                        ref_id=ec.id,
                    )
                    db.add(act)
                    db.commit()
                    logger.info("Stripe webhook: member_ecoupon customer_id=%s amount=%.2f code=%s", customer_id, amount_baht, code)
            else:
                logger.warning("Stripe webhook: member intent customer_id=%s not found", customer_id)
        return {"received": True}

    if not ref1:
        logger.warning("Stripe webhook: payment_intent %s has no metadata.ref1 or member metadata", data.get("id"))
        return {"received": True}
    logger.info("Stripe webhook: payment_intent.succeeded ref1=%s amount=%.2f", ref1[:20], amount_baht)
    payload = BackTransactionPayload(ref1=ref1, amount=amount_baht, raw_payload=body)
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
