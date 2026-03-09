"""
Stripe QR PromptPay – สร้าง PaymentIntent แบบ PromptPay และรับ Webhook
อ้างอิง: https://docs.stripe.com/payments/promptpay, https://docs.stripe.com/api/payment_intents/create
- สร้าง PaymentIntent: POST https://api.stripe.com/v1/payment_intents
  amount (satang), currency=thb, payment_method_types[]=promptpay
- ลูกค้าใช้ client_secret กับ Stripe.js / Payment Element เพื่อแสดง QR หรือใช้ redirect
- Webhook: payment_intent.succeeded
"""
import logging
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)
STRIPE_API = "https://api.stripe.com/v1"


def create_payment_intent_promptpay(
    secret_key: str,
    amount_satang: int,
    currency: str = "thb",
    metadata: Optional[Dict[str, str]] = None,
    return_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    สร้าง Stripe PaymentIntent สำหรับ PromptPay
    amount_satang: จำนวนเงินเป็นสตางค์ (เช่น 10000 = 100 บาท)
    คืน PaymentIntent; ใช้ client_secret สำหรับ frontend แสดง QR ผ่าน Stripe.js
    """
    return create_payment_intent(
        secret_key=secret_key,
        amount_satang=amount_satang,
        payment_method_types=["promptpay"],
        currency=currency,
        metadata=metadata,
        return_url=return_url,
    )


def create_payment_intent(
    secret_key: str,
    amount_satang: int,
    payment_method_types: list,
    currency: str = "thb",
    metadata: Optional[Dict[str, str]] = None,
    return_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    สร้าง Stripe PaymentIntent (รองรับ promptpay, apple_pay, card ฯลฯ)
    payment_method_types: เช่น ["promptpay"], ["apple_pay"], ["card", "apple_pay"]
    อ้างอิง: https://docs.stripe.com/api, https://docs.stripe.com/payments/apple-pay
    """
    url = f"{STRIPE_API}/payment_intents"
    headers = {"Authorization": f"Bearer {secret_key}", "Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "amount": str(amount_satang),
        "currency": currency.lower(),
    }
    for i, pm in enumerate(payment_method_types):
        data[f"payment_method_types[{i}]"] = pm
    if metadata:
        for k, v in metadata.items():
            data[f"metadata[{k}]"] = str(v)
    # return_url ใช้เฉพาะตอน confirm (client-side confirmPayment) ไม่ส่งตอน create
    # มิฉะนั้น Stripe จะ error: return_url cannot be passed unless confirm is true

    logger.info("Stripe API: POST payment_intents amount=%s methods=%s", amount_satang, payment_method_types)
    with httpx.Client(timeout=15.0) as client:
        resp = client.post(url, headers=headers, data=data)
    logger.info("Stripe API response: payment_intents status=%s", resp.status_code)

    if resp.status_code not in (200, 201):
        logger.warning("Stripe PaymentIntent failed: %s %s", resp.status_code, resp.text[:500])
        raise ValueError(f"Stripe PaymentIntent failed: {resp.status_code} {resp.text}")

    return resp.json()


def create_payment_intent_apple_pay(
    secret_key: str,
    amount_satang: int,
    currency: str = "thb",
    metadata: Optional[Dict[str, str]] = None,
    return_url: Optional[str] = None,
) -> Dict[str, Any]:
    """สร้าง Stripe PaymentIntent สำหรับ Apple Pay (https://docs.stripe.com/payments/apple-pay)"""
    return create_payment_intent(
        secret_key=secret_key,
        amount_satang=amount_satang,
        payment_method_types=["apple_pay"],
        currency=currency,
        metadata=metadata,
        return_url=return_url,
    )


def retrieve_payment_intent(secret_key: str, payment_intent_id: str) -> Dict[str, Any]:
    """ดึง PaymentIntent จาก Stripe"""
    url = f"{STRIPE_API}/payment_intents/{payment_intent_id}"
    headers = {"Authorization": f"Bearer {secret_key}"}
    with httpx.Client(timeout=10.0) as client:
        resp = client.get(url, headers=headers)
    if resp.status_code != 200:
        raise ValueError(f"Stripe get PaymentIntent failed: {resp.status_code}")
    return resp.json()


def confirm_payment_intent_promptpay(
    secret_key: str,
    payment_intent_id: str,
    email: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Confirm PaymentIntent สำหรับ PromptPay (server-side).
    หลัง confirm แล้ว Stripe จะคืน next_action.promptpay_display_qr_code ที่มี data (plain text สำหรับสร้าง QR).
    """
    url = f"{STRIPE_API}/payment_intents/{payment_intent_id}/confirm"
    headers = {"Authorization": f"Bearer {secret_key}", "Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "payment_method_data[type]": "promptpay",
        "payment_method_data[billing_details][email]": email or "noreply@store.local",
    }
    logger.info("Stripe API: POST payment_intents/%s/confirm (promptpay)", payment_intent_id)
    with httpx.Client(timeout=15.0) as client:
        resp = client.post(url, headers=headers, data=data)
    logger.info("Stripe API response: confirm status=%s", resp.status_code)
    if resp.status_code != 200:
        logger.warning("Stripe confirm failed: %s %s", resp.status_code, resp.text[:500])
        raise ValueError(f"Stripe confirm failed: {resp.status_code} {resp.text}")
    return resp.json()


def get_promptpay_qr_data_from_payment_intent(pi: Dict[str, Any]) -> Optional[str]:
    """
    ดึง plain text สำหรับสร้าง QR จาก PaymentIntent หลัง confirm แล้ว (status requires_action).
    คืนค่า next_action.promptpay_display_qr_code.data หรือ None ถ้าไม่มี
    """
    next_action = pi.get("next_action") or {}
    qr_action = next_action.get("promptpay_display_qr_code") or next_action.get("promptpayDisplayQrCode")
    if not qr_action:
        logger.debug("Stripe PI next_action has no promptpay_display_qr_code: %s", list(next_action.keys()) if next_action else "empty")
        return None
    data = qr_action.get("data")
    if not data:
        logger.warning("Stripe promptpay_display_qr_code has no 'data': %s", list(qr_action.keys()) if isinstance(qr_action, dict) else type(qr_action))
    return data


def get_promptpay_qr_image_url_from_payment_intent(pi: Dict[str, Any]) -> Optional[str]:
    """
    ดึง URL รูป QR จาก next_action.promptpay_display_qr_code (image_url_png หรือ image_url_svg).
    ใช้เป็น fallback เมื่อไม่มี data (plain text) สำหรับสร้าง QR ฝั่ง client
    """
    next_action = pi.get("next_action") or {}
    qr_action = next_action.get("promptpay_display_qr_code") or next_action.get("promptpayDisplayQrCode")
    if not qr_action or not isinstance(qr_action, dict):
        return None
    return (
        qr_action.get("image_url_png")
        or qr_action.get("imageUrlPng")
        or qr_action.get("image_url_svg")
        or qr_action.get("imageUrlSvg")
    )


def list_webhook_endpoints(secret_key: str) -> list:
    """ดึงรายการ webhook endpoints จาก Stripe"""
    url = f"{STRIPE_API}/webhook_endpoints"
    headers = {"Authorization": f"Bearer {secret_key}"}
    with httpx.Client(timeout=10.0) as client:
        resp = client.get(url, params={"limit": "100"})
    if resp.status_code != 200:
        raise ValueError(f"Stripe list webhooks failed: {resp.status_code} {resp.text}")
    data = resp.json()
    return data.get("data") or []


def update_webhook_endpoint_url(secret_key: str, endpoint_id: str, new_url: str) -> Dict[str, Any]:
    """อัปเดต URL ของ webhook endpoint ที่ Stripe"""
    url = f"{STRIPE_API}/webhook_endpoints/{endpoint_id}"
    headers = {"Authorization": f"Bearer {secret_key}", "Content-Type": "application/x-www-form-urlencoded"}
    data = {"url": new_url}
    with httpx.Client(timeout=10.0) as client:
        resp = client.post(url, headers=headers, data=data)
    if resp.status_code != 200:
        raise ValueError(f"Stripe update webhook failed: {resp.status_code} {resp.text}")
    return resp.json()
