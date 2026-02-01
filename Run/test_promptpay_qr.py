"""
Test script สำหรับทดสอบ PromptPay QR Code Generation
"""
import sys
from pathlib import Path

# เพิ่ม root directory เข้า Python path
root_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(root_dir))

from app.services.promptpay import generate_promptpay_qr_content, generate_promptpay_qr_image

def test_promptpay_qr():
    """ทดสอบการสร้าง PromptPay QR Code"""
    
    print("=" * 60)
    print("Testing PromptPay QR Code Generation")
    print("=" * 60)
    
    # Test Case 1: Basic QR Code with all fields
    print("\n1. Testing with all fields:")
    try:
        qr_content = generate_promptpay_qr_content(
            biller_id="123456789012399",  # tax_id + "99"
            ref1="1",  # store.id
            ref2="5",  # menu.id
            ref3="ทดสอบ",  # remark
            amount=90.00
        )
        print(f"✅ QR Content: {qr_content}")
        print(f"   Length: {len(qr_content)} characters")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test Case 2: QR Code without optional fields
    print("\n2. Testing without optional fields:")
    try:
        qr_content = generate_promptpay_qr_content(
            biller_id="123456789012399",
            ref1="1",
            ref2=None,
            ref3=None,
            amount=100.00
        )
        print(f"✅ QR Content: {qr_content}")
        print(f"   Length: {len(qr_content)} characters")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test Case 3: QR Code without amount
    print("\n3. Testing without amount:")
    try:
        qr_content = generate_promptpay_qr_content(
            biller_id="123456789012399",
            ref1="1",
            ref2=None,
            ref3=None,
            amount=None
        )
        print(f"✅ QR Content: {qr_content}")
        print(f"   Length: {len(qr_content)} characters")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test Case 4: Generate QR Image
    print("\n4. Testing QR Image generation:")
    try:
        qr_image = generate_promptpay_qr_image(
            biller_id="123456789012399",
            ref1="1",
            ref2="5",
            ref3="ทดสอบ",
            amount=90.00,
            size=300
        )
        print(f"✅ QR Image generated (Base64 length: {len(qr_image)} characters)")
        print(f"   Preview: {qr_image[:50]}...")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test Case 5: Invalid biller_id
    print("\n5. Testing with invalid biller_id:")
    try:
        qr_content = generate_promptpay_qr_content(
            biller_id="",  # Empty
            ref1="1",
            amount=100.00
        )
        print(f"❌ Should have raised error but got: {qr_content}")
    except ValueError as e:
        print(f"✅ Correctly caught error: {e}")
    except Exception as e:
        print(f"⚠️  Unexpected error: {e}")
    
    # Test Case 6: Invalid ref1
    print("\n6. Testing with invalid ref1:")
    try:
        qr_content = generate_promptpay_qr_content(
            biller_id="123456789012399",
            ref1="",  # Empty
            amount=100.00
        )
        print(f"❌ Should have raised error but got: {qr_content}")
    except ValueError as e:
        print(f"✅ Correctly caught error: {e}")
    except Exception as e:
        print(f"⚠️  Unexpected error: {e}")
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)

if __name__ == "__main__":
    test_promptpay_qr()

