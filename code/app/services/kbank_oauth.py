"""
K Bank (K API) OAuth 2.0 – ดึง Access Token สำหรับ Inward Remittance / QR Payment
อ้างอิง:
- IDENTITY: https://apiportal.kasikornbank.com/product/public/Fund%20Transfer/Inward%20Remittance/Documentation/IDENTITY
- OAuth 2.0 Try API: https://apiportal.kasikornbank.com/product/public/Fund%20Transfer/Inward%20Remittance/Try%20API/OAuth%202.0
- ข้อมูลจาก K_API.note: CUSTOMER ID (client_id), CONSUMER SECRET (client_secret), grant_type=client_credentials
"""
import base64
import logging
import time
from typing import Optional, Tuple

import httpx

logger = logging.getLogger(__name__)

from app.config import (
    KBANK_CUSTOMER_ID,
    KBANK_CONSUMER_SECRET,
    KBANK_OAUTH_TOKEN_URL,
)

# Cache ในหน่วย process (token, expiry timestamp)
_cached_token: Optional[str] = None
_cached_expiry: float = 0
_cached_credentials: Tuple[str, str] = ("", "")


def get_access_token(
    customer_id: Optional[str] = None,
    consumer_secret: Optional[str] = None,
    token_url: Optional[str] = None,
    use_cache: bool = True,
) -> str:
    """
    ดึง OAuth 2.0 access_token จาก K Bank (client_credentials).
    ใช้ CUSTOMER ID และ CONSUMER SECRET จาก K_API.note เป็น client_id / client_secret
    Authorization: Basic base64(customer_id:consumer_secret)
    Body: grant_type=client_credentials

    :param customer_id: ค่าจาก K_API.note (CUSTOMER ID); ไม่ส่งใช้จาก config
    :param consumer_secret: ค่าจาก K_API.note (CONSUMER SECRET); ไม่ส่งใช้จาก config
    :param token_url: URL สำหรับขอ token; ไม่ส่งใช้จาก config (Sandbox default)
    :param use_cache: ใช้ token ที่ cache ไว้จนกว่าจะใกล้หมดอายุ (expires_in - 60 วินาที)
    :return: access_token (Bearer) สำหรับใส่ Header เรียก K API อื่น
    :raises ValueError: ถ้าไม่มี customer_id/consumer_secret หรือ token API คืน error
    """
    global _cached_token, _cached_expiry, _cached_credentials

    cid = (customer_id or KBANK_CUSTOMER_ID or "").strip()
    secret = (consumer_secret or KBANK_CONSUMER_SECRET or "").strip()
    if not cid or not secret:
        raise ValueError("K Bank OAuth ต้องการ KBANK_CUSTOMER_ID และ KBANK_CONSUMER_SECRET (จาก K_API.note หรือ config)")

    url = token_url or KBANK_OAUTH_TOKEN_URL
    cred_key = (cid, secret)
    now = time.time()

    if use_cache and _cached_token and cred_key == _cached_credentials and now < _cached_expiry:
        logger.debug("K Bank OAuth: using cached token")
        return _cached_token

    # Basic = Base64(customer_id:consumer_secret)
    raw = f"{cid}:{secret}"
    b64 = base64.b64encode(raw.encode("utf-8")).decode("ascii")
    headers = {"Authorization": f"Basic {b64}", "Content-Type": "application/x-www-form-urlencoded"}
    data = {"grant_type": "client_credentials"}

    logger.info("K Bank API call: oauth/token POST %s", url)
    with httpx.Client(timeout=15.0) as client:
        resp = client.post(url, headers=headers, data=data)
    logger.info("K Bank API response: oauth/token status=%s", resp.status_code)

    if resp.status_code != 200:
        logger.warning("K Bank OAuth failed: status=%s body=%s", resp.status_code, resp.text[:500])
        raise ValueError(f"K Bank OAuth token failed: {resp.status_code} {resp.text}")

    body = resp.json()
    token = body.get("access_token")
    if not token:
        raise ValueError(f"K Bank OAuth response ไม่มี access_token: {body}")

    expires_in = int(body.get("expires_in", 1799))  # ตัวอย่างจาก K_API.note = 1799
    _cached_token = token
    _cached_expiry = now + expires_in - 60  # หมดก่อน 60 วินาที
    _cached_credentials = cred_key

    logger.info("K Bank OAuth: token obtained, expires_in=%s", expires_in)
    return token


def clear_token_cache() -> None:
    """ล้าง cache token (ใช้เมื่อเปลี่ยน credentials หรือทดสอบ)"""
    global _cached_token, _cached_expiry, _cached_credentials
    _cached_token = None
    _cached_expiry = 0
    _cached_credentials = ("", "")
