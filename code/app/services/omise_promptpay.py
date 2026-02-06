"""
Omise QR PromptPay – สร้าง Charge แบบ PromptPay และรับ Webhook
อ้างอิง: https://docs.omise.co/promptpay
- สร้าง Charge: POST https://api.omise.co/charges (Basic auth ด้วย secret key)
  body: amount (satang), currency=THB, source[type]=promptpay
- QR image อยู่ที่ charge.source.scannable_code.image.download_uri
- Webhook: charge.complete → ตรวจสอบ charge.status == successful
"""
import base64
import logging
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)
OMISE_API = "https://api.omise.co"


def create_charge_promptpay(
    secret_key: str,
    amount_satang: int,
    currency: str = "THB",
    metadata: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    สร้าง Omise Charge แบบ PromptPay (QR)
    amount_satang: จำนวนเงินเป็นสตางค์ (เช่น 10000 = 100 บาท)
    คืน charge object; QR image ที่ charge.source.scannable_code.image.download_uri
    """
    url = f"{OMISE_API}/charges"
    auth = base64.b64encode(f"{secret_key}:".encode()).decode()
    headers = {"Authorization": f"Basic {auth}", "Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "amount": str(amount_satang),
        "currency": currency.lower(),
        "source[type]": "promptpay",
    }
    if metadata:
        for k, v in metadata.items():
            data[f"metadata[{k}]"] = str(v)

    logger.info("Omise API: POST /charges amount=%s satang", amount_satang)
    with httpx.Client(timeout=15.0) as client:
        resp = client.post(url, headers=headers, data=data)
    logger.info("Omise API response: charges status=%s", resp.status_code)

    if resp.status_code not in (200, 201):
        logger.warning("Omise charge failed: %s %s", resp.status_code, resp.text[:500])
        raise ValueError(f"Omise charge failed: {resp.status_code} {resp.text}")

    out = resp.json()
    qr_uri = None
    try:
        src = out.get("source") or {}
        scannable = src.get("scannable_code") or {}
        img = scannable.get("image") or {}
        qr_uri = img.get("download_uri")
    except Exception:
        pass
    out["_qr_download_uri"] = qr_uri
    return out


def get_charge(secret_key: str, charge_id: str) -> Dict[str, Any]:
    """ดึง charge จาก Omise"""
    url = f"{OMISE_API}/charges/{charge_id}"
    auth = base64.b64encode(f"{secret_key}:".encode()).decode()
    headers = {"Authorization": f"Basic {auth}"}
    with httpx.Client(timeout=10.0) as client:
        resp = client.get(url, headers=headers)
    if resp.status_code != 200:
        raise ValueError(f"Omise get charge failed: {resp.status_code}")
    return resp.json()
