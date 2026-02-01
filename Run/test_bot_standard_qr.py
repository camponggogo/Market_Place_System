"""
Test script สำหรับทดสอบ QR Code ตามมาตรฐาน BOT
- แบบ 362 ตัวอักษร (แบบเต็ม)
- แบบ 62 ตัวอักษร (แบบสั้น)
- Tag29 (Credit Transfer)
- Tag30 (Bill Payment)
"""
import sys
from pathlib import Path

# เพิ่ม root directory เข้า Python path
root_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(root_dir))

from app.services.promptpay_bot_standard import (
    generate_bot_standard_qr_362,
    generate_bot_standard_qr_62,
    generate_bot_qr_image
)
from app.services.promptpay import (
    generate_promptpay_qr_content,
    generate_promptpay_credit_transfer_content,
    generate_promptpay_qr_image,
    generate_promptpay_credit_transfer_image
)

def test_all_qr_types():
    """ทดสอบ QR Code ทั้ง 4 แบบ"""
    
    print("=" * 80)
    print("ทดสอบ QR Code ตามมาตรฐาน BOT")
    print("=" * 80)
    
    # ข้อมูลทดสอบ
    biller_id = "123456789012399"
    ref1 = "STORE001"
    ref2 = "MENU005"
    ref3 = "INV2024001"
    amount = 100.50
    
    # ข้อมูลผู้ซื้อ (สำหรับแบบ 362 ตัวอักษร)
    buyer_name = "นายทดสอบ ระบบ"
    buyer_address = "123 ถนนทดสอบ แขวงทดสอบ"
    buyer_city = "ตำบลทดสอบ"
    buyer_province = "อำเภอทดสอบ"
    buyer_postcode = "10100"
    buyer_country = "THAILAND"
    type_of_income = "001"  # ค่าสินค้า
    
    # ==========================================
    # 1. Tag30 - Bill Payment แบบ 362 ตัวอักษร (แบบเต็ม)
    # ==========================================
    print("\n" + "=" * 80)
    print("1. Tag30 - Bill Payment แบบ 362 ตัวอักษร (แบบเต็ม)")
    print("=" * 80)
    
    try:
        qr_content_362 = generate_bot_standard_qr_362(
            biller_id=biller_id,
            ref1=ref1,
            ref2=ref2,
            ref3=ref3,
            amount=amount,
            buyer_name=buyer_name,
            buyer_address=buyer_address,
            buyer_city=buyer_city,
            buyer_province=buyer_province,
            buyer_postcode=buyer_postcode,
            buyer_country=buyer_country,
            type_of_income=type_of_income
        )
        
        print(f"✅ QR Content (362 chars):")
        print(f"   Length: {len(qr_content_362)} characters")
        print(f"   Content: {qr_content_362[:100]}...")
        
        # สร้าง QR Image
        qr_image_362 = generate_bot_qr_image(qr_content_362)
        print(f"✅ QR Image generated (Base64 length: {len(qr_image_362)} characters)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # ==========================================
    # 2. Tag30 - Bill Payment แบบ 62 ตัวอักษร (แบบสั้น)
    # ==========================================
    print("\n" + "=" * 80)
    print("2. Tag30 - Bill Payment แบบ 62 ตัวอักษร (แบบสั้น)")
    print("=" * 80)
    
    try:
        qr_content_62 = generate_bot_standard_qr_62(
            biller_id=biller_id,
            ref1=ref1,
            ref2=ref2,
            ref3=ref3,
            amount=amount
        )
        
        print(f"✅ QR Content (62 chars):")
        print(f"   Length: {len(qr_content_62)} characters")
        print(f"   Content: {qr_content_62}")
        
        # สร้าง QR Image
        qr_image_62 = generate_bot_qr_image(qr_content_62)
        print(f"✅ QR Image generated (Base64 length: {len(qr_image_62)} characters)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # ==========================================
    # 3. Tag30 - Bill Payment (แบบเดิม)
    # ==========================================
    print("\n" + "=" * 80)
    print("3. Tag30 - Bill Payment (แบบเดิม)")
    print("=" * 80)
    
    try:
        qr_content_tag30 = generate_promptpay_qr_content(
            biller_id=biller_id,
            ref1=ref1,
            ref2=ref2,
            ref3=ref3,
            amount=amount
        )
        
        print(f"✅ QR Content (Tag30):")
        print(f"   Length: {len(qr_content_tag30)} characters")
        print(f"   Content: {qr_content_tag30[:100]}...")
        
        # สร้าง QR Image
        qr_image_tag30 = generate_promptpay_qr_image(
            biller_id=biller_id,
            ref1=ref1,
            ref2=ref2,
            ref3=ref3,
            amount=amount
        )
        print(f"✅ QR Image generated (Base64 length: {len(qr_image_tag30)} characters)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # ==========================================
    # 4. Tag29 - Credit Transfer
    # ==========================================
    print("\n" + "=" * 80)
    print("4. Tag29 - Credit Transfer")
    print("=" * 80)
    
    try:
        mobile_number = "0812345678"
        qr_content_tag29 = generate_promptpay_credit_transfer_content(
            mobile_number=mobile_number,
            amount=amount
        )
        
        print(f"✅ QR Content (Tag29):")
        print(f"   Length: {len(qr_content_tag29)} characters")
        print(f"   Content: {qr_content_tag29[:100]}...")
        
        # สร้าง QR Image
        qr_image_tag29 = generate_promptpay_credit_transfer_image(
            mobile_number=mobile_number,
            amount=amount
        )
        print(f"✅ QR Image generated (Base64 length: {len(qr_image_tag29)} characters)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("สรุปผลการทดสอบ")
    print("=" * 80)
    print("1. Tag30 - Bill Payment แบบ 362 ตัวอักษร (แบบเต็ม)")
    print("2. Tag30 - Bill Payment แบบ 62 ตัวอักษร (แบบสั้น)")
    print("3. Tag30 - Bill Payment (แบบเดิม)")
    print("4. Tag29 - Credit Transfer")
    print("\n✅ ทดสอบเสร็จสิ้น! ลองสแกน QR Code ทั้ง 4 แบบ")

if __name__ == "__main__":
    test_all_qr_types()

