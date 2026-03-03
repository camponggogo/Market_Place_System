"""
ทดสอบ SCB QR Code และ Webhook API ด้วย API Key
ใช้: python Run/test_scb_api.py
หรือ: python Run/test_scb_api.py --amount 100
"""
import sys
import argparse
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / "code"))

# Test credentials (จาก scb.note / SCB Developer)
APP_NAME = "QR-PromptPay-1"
API_KEY = "l79417b2c08a8c42b9b7d5c51210c01dbc"
API_SECRET = "9e96ab1086634cf4b7e4001ffec50908"


def main():
    parser = argparse.ArgumentParser(description="Test SCB QR/Webhook API")
    parser.add_argument("--amount", type=float, default=1.00, help="Amount (THB) for test transaction")
    parser.add_argument("--callback", type=str, default="", help="Webhook callback URL (default: from config)")
    args = parser.parse_args()

    from app.config import BACKEND_URL
    from app.services.scb_deeplink import get_oauth_token, create_deeplink_transaction

    callback_url = args.callback or f"{BACKEND_URL.rstrip('/')}/api/payment-callback/webhook"
    ref1 = "00000000000010000000"  # 20 หลัก store token ตัวอย่าง

    print("=" * 60)
    print("SCB QR Code & Webhook - Test API")
    print("=" * 60)
    print(f"App Name: {APP_NAME}")
    print(f"API Key:  {API_KEY[:16]}...")
    print(f"Amount:   {args.amount} THB")
    print(f"Callback: {callback_url}")
    print()

    try:
        print("1. OAuth Token...")
        token = get_oauth_token(API_KEY, API_SECRET)
        print("   OK - token received")

        print("2. Create Deeplink Transaction (QR)...")
        result = create_deeplink_transaction(
            access_token=token,
            api_key=API_KEY,
            payment_amount=args.amount,
            ref1=ref1,
            ref2="TEST001",
            callback_url=callback_url,
            merchant_name="Test Store",
        )
        print("   OK - transaction created")

        data = result.get("data") or result
        qr_code = data.get("qrCode") or data.get("qr_code")
        deeplink = data.get("deeplinkUrl") or data.get("deeplink_url")
        txn_id = data.get("transactionId") or data.get("transaction_id")

        print()
        print("Result:")
        if txn_id:
            print(f"  Transaction ID: {txn_id}")
        if deeplink:
            print(f"  Deeplink URL:   {deeplink[:60]}...")
        if qr_code:
            if qr_code.startswith("data:"):
                print(f"  QR Code:        [base64 image, {len(qr_code)} chars]")
            else:
                print(f"  QR Code:        {qr_code[:80]}...")

        print()
        print("Success! ใช้ Deeplink หรือ QR สำหรับทดสอบชำระเงิน")
        return 0

    except ValueError as e:
        print(f"Error: {e}")
        print("  หมายเหตุ: ให้ลงทะเบียน Callback URL ที่ SCB Developer และตรวจสอบ accountTo (biller_id)")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
