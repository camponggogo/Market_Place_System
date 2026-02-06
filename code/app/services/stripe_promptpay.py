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
    if return_url:
        data["return_url"] = return_url

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
