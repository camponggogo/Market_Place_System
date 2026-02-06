"""
SCB Partners API – Deeplink for Payment
โครงสร้างเรียก API ตาม Postman (scb_deeplink-transaction.json):
- OAuth: POST /partners/sandbox/v1/oauth/token
- Deeplink: POST /partners/sandbox/v3/deeplink/transactions (callbackUrl ใน merchantMetaData = webhook SCB เท่านั้น)
- Get transaction: GET /partners/sandbox/v2/transactions/{transactionId}
อ้างอิง: https://developer.scb/
"""
import logging
import uuid
from typing import Any, Dict, Optional

import httpx

from app.config import SCB_BASE_URL

logger = logging.getLogger(__name__)


def _base(base_url: Optional[str] = None) -> str:
    return (base_url or SCB_BASE_URL or "").rstrip("/")


def get_oauth_token(
    api_key: str,
    api_secret: str,
    base_url: Optional[str] = None,
) -> str:
    """
    1. OAuth Token – ตาม Postman "1. /partners/sandbox/v1/oauth/token"
    Headers: Content-Type application/json, resourceOwnerId (API Key), requestUId (guid), accept-language EN
    Body: applicationKey, applicationSecret
    """
    base = _base(base_url)
    url = f"{base}/partners/sandbox/v1/oauth/token"
    headers = {
        "Content-Type": "application/json",
        "resourceOwnerId": api_key,
        "requestUId": str(uuid.uuid4()),
        "accept-language": "EN",
    }
    body = {
        "applicationKey": api_key,
        "applicationSecret": api_secret,
    }
    logger.info("SCB API call: oauth/token POST %s", url)
    with httpx.Client(timeout=15.0) as client:
        resp = client.post(url, json=body, headers=headers)
    logger.info("SCB API response: oauth/token status=%s", resp.status_code)
    if resp.status_code != 200:
        logger.warning("SCB OAuth failed: status=%s body=%s", resp.status_code, resp.text[:500])
        raise ValueError(f"SCB OAuth failed: {resp.status_code} {resp.text}")
    data = resp.json()
    token = data.get("data", {}).get("accessToken") or data.get("accessToken")
    if not token:
        logger.warning("SCB OAuth no accessToken in response")
        raise ValueError(f"SCB OAuth ไม่มี accessToken: {data}")
    return token


def create_deeplink_transaction(
    access_token: str,
    api_key: str,
    payment_amount: float,
    ref1: str,
    ref2: Optional[str] = None,
    ref3: Optional[str] = None,
    account_to: Optional[str] = None,
    account_from: Optional[str] = None,
    callback_url: Optional[str] = None,
    session_validity_period: int = 60,
    channel: str = "scbeasy",
    base_url: Optional[str] = None,
    merchant_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    2. Deeplink Transactions – ตาม Postman "2. /partners/sandbox/v3/deeplink/transactions"
    callbackUrl ใน merchantMetaData = URL webhook ของ SCB เท่านั้น (แยกจาก K Bank)
    """
    base = _base(base_url)
    url = f"{base}/partners/sandbox/v3/deeplink/transactions"
    headers = {
        "Content-Type": "application/json",
        "authorization": f"Bearer {access_token}",
        "resourceOwnerId": api_key,
        "requestUId": str(uuid.uuid4()),
        "channel": channel,
        "accept-language": "EN",
    }
    # โครงสร้าง body ตาม Postman
    body = {
        "transactionType": "PURCHASE",
        "transactionSubType": ["BP", "CCFA", "CCIPP"],
        "sessionValidityPeriod": session_validity_period,
        "sessionValidUntil": "",
        "billPayment": {
            "paymentAmount": payment_amount,
            "accountTo": account_to or "123456789012345",
            "accountFrom": account_from or "123451234567890",
            "ref1": ref1,
            "ref2": ref2 or ref1,
            "ref3": ref3 or "",
        },
        "creditCardFullAmount": {
            "merchantId": "1234567890ABCDEF",
            "terminalId": "1234ABCD",
            "orderReference": "12345678",
            "paymentAmount": payment_amount,
        },
        "installmentPaymentPlan": {
            "merchantId": "4218170000000160",
            "terminalId": "56200004",
            "orderReference": "AA100001",
            "paymentAmount": 10000.00,
            "tenor": "12",
            "ippType": "3",
            "prodCode": "1001",
        },
        "merchantMetaData": {
            "callbackUrl": callback_url or "",
            "merchantInfo": {
                "name": merchant_name or "MERCHANT",
            },
            "extraData": {},
            "paymentInfo": [
                {"type": "TEXT_WITH_IMAGE", "title": "", "header": "", "description": "", "imageUrl": ""},
                {"type": "TEXT", "title": "", "header": "", "description": ""},
            ],
        },
    }
    logger.info("SCB API call: deeplink/transactions POST %s amount=%.2f ref1=%s", url, payment_amount, ref1[:20] + "..." if len(ref1) > 20 else ref1)
    with httpx.Client(timeout=15.0) as client:
        resp = client.post(url, json=body, headers=headers)
    logger.info("SCB API response: deeplink/transactions status=%s", resp.status_code)
    if resp.status_code not in (200, 201):
        logger.warning("SCB deeplink failed: status=%s body=%s", resp.status_code, resp.text[:500])
        raise ValueError(f"SCB deeplink failed: {resp.status_code} {resp.text}")
    return resp.json()


def get_transaction(
    access_token: str,
    api_key: str,
    transaction_id: str,
    base_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    3. Get Transaction – ตาม Postman "3. /partners/sandbox/v2/transactions/{transactionId}"
    """
    base = _base(base_url)
    url = f"{base}/partners/sandbox/v2/transactions/{transaction_id}"
    headers = {
        "authorization": f"Bearer {access_token}",
        "resourceOwnerId": api_key,
        "requestUId": str(uuid.uuid4()),
        "accept-language": "EN",
    }
    logger.info("SCB API call: transactions GET %s", url)
    with httpx.Client(timeout=15.0) as client:
        resp = client.get(url, headers=headers)
    logger.info("SCB API response: transactions/%s status=%s", transaction_id, resp.status_code)
    if resp.status_code != 200:
        logger.warning("SCB get transaction failed: status=%s body=%s", resp.status_code, resp.text[:500])
        raise ValueError(f"SCB get transaction failed: {resp.status_code} {resp.text}")
    return resp.json()
