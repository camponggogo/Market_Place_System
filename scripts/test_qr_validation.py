"""
Test script สำหรับตรวจสอบ QR Code PromptPay
เปรียบเทียบกับตัวอย่างที่ทำงานได้จริง
"""
import sys
from pathlib import Path

# เพิ่ม root directory เข้า Python path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from app.services.promptpay import (
    generate_promptpay_qr_content,
    generate_promptpay_credit_transfer_content,
    calculate_crc16,
    format_tag
)

def test_simple_tag29():
    """ทดสอบ Tag29 แบบง่ายที่สุด"""
    print("=" * 80)
    print("Test Tag29 - Simple (Mobile Number Only)")
    print("=" * 80)
    
    try:
        # สร้าง QR Code แบบง่ายที่สุด - Mobile Number ไม่มี amount
        qr_content = generate_promptpay_credit_transfer_content(
            mobile_number="0812345678",
            amount=None
        )
        
        print(f"\n✅ QR Content:")
        print(f"{qr_content}")
        print(f"\nLength: {len(qr_content)} characters")
        
        # แสดง breakdown
        print(f"\nBreakdown:")
        i = 0
        while i < len(qr_content):
            if i + 4 <= len(qr_content):
                tag = qr_content[i:i+2]
                length_str = qr_content[i+2:i+4]
                try:
                    length = int(length_str)
                    value = qr_content[i+4:i+4+length]
                    print(f"  Tag {tag}: Length={length_str} ({length}), Value='{value}'")
                    i += 4 + length
                except Exception as e:
                    print(f"  Error parsing at position {i}: {e}")
                    break
            else:
                break
        
        # ตรวจสอบ CRC16 (EMV: คำนวณบน payload + "6304")
        crc_tag_pos = qr_content.rfind("63")
        if crc_tag_pos != -1:
            payload_without_crc = qr_content[:crc_tag_pos]
            crc_length_str = qr_content[crc_tag_pos+2:crc_tag_pos+4]
            crc_length = int(crc_length_str)
            crc_from_qr = qr_content[crc_tag_pos+4:crc_tag_pos+4+crc_length]
            
            # คำนวณ CRC16 ใหม่
            payload_bytes = (payload_without_crc + "6304").encode('utf-8')
            calculated_crc_ccitt = calculate_crc16(payload_bytes, use_ccitt=True)
            calculated_crc_custom = calculate_crc16(payload_bytes, use_ccitt=False)
            
            print(f"\nCRC16 Check:")
            print(f"  CRC in QR: {crc_from_qr}")
            print(f"  Calculated CRC (CCITT): {calculated_crc_ccitt:04X}")
            print(f"  Calculated CRC (Custom): {calculated_crc_custom:04X}")
            print(f"  Match (CCITT): {'✅' if crc_from_qr == f'{calculated_crc_ccitt:04X}' else '❌'}")
            print(f"  Match (Custom): {'✅' if crc_from_qr == f'{calculated_crc_custom:04X}' else '❌'}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


def test_simple_tag30():
    """ทดสอบ Tag30 แบบง่ายที่สุด"""
    print("\n" + "=" * 80)
    print("Test Tag30 - Simple (Biller ID + Ref1 Only)")
    print("=" * 80)
    
    try:
        # สร้าง QR Code แบบง่ายที่สุด - ไม่มี ref2, ref3, amount
        qr_content = generate_promptpay_qr_content(
            biller_id="123456789012399",
            ref1="1",
            ref2=None,
            ref3=None,
            amount=None
        )
        
        print(f"\n✅ QR Content:")
        print(f"{qr_content}")
        print(f"\nLength: {len(qr_content)} characters")
        
        # แสดง breakdown
        print(f"\nBreakdown:")
        i = 0
        while i < len(qr_content):
            if i + 4 <= len(qr_content):
                tag = qr_content[i:i+2]
                length_str = qr_content[i+2:i+4]
                try:
                    length = int(length_str)
                    value = qr_content[i+4:i+4+length]
                    print(f"  Tag {tag}: Length={length_str} ({length}), Value='{value}'")
                    i += 4 + length
                except Exception as e:
                    print(f"  Error parsing at position {i}: {e}")
                    break
            else:
                break
        
        # ตรวจสอบ CRC16 (EMV: คำนวณบน payload + "6304")
        crc_tag_pos = qr_content.rfind("63")
        if crc_tag_pos != -1:
            payload_without_crc = qr_content[:crc_tag_pos]
            crc_length_str = qr_content[crc_tag_pos+2:crc_tag_pos+4]
            crc_length = int(crc_length_str)
            crc_from_qr = qr_content[crc_tag_pos+4:crc_tag_pos+4+crc_length]
            
            # คำนวณ CRC16 ใหม่
            payload_bytes = (payload_without_crc + "6304").encode('utf-8')
            calculated_crc_ccitt = calculate_crc16(payload_bytes, use_ccitt=True)
            calculated_crc_custom = calculate_crc16(payload_bytes, use_ccitt=False)
            
            print(f"\nCRC16 Check:")
            print(f"  CRC in QR: {crc_from_qr}")
            print(f"  Calculated CRC (CCITT): {calculated_crc_ccitt:04X}")
            print(f"  Calculated CRC (Custom): {calculated_crc_custom:04X}")
            print(f"  Match (CCITT): {'✅' if crc_from_qr == f'{calculated_crc_ccitt:04X}' else '❌'}")
            print(f"  Match (Custom): {'✅' if crc_from_qr == f'{calculated_crc_custom:04X}' else '❌'}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


def test_with_amount():
    """ทดสอบ Tag30 พร้อม amount"""
    print("\n" + "=" * 80)
    print("Test Tag30 - With Amount")
    print("=" * 80)
    
    try:
        qr_content = generate_promptpay_qr_content(
            biller_id="123456789012399",
            ref1="1",
            ref2=None,
            ref3=None,
            amount=100.50
        )
        
        print(f"\n✅ QR Content:")
        print(f"{qr_content}")
        print(f"\nLength: {len(qr_content)} characters")
        
        # ตรวจสอบว่ามี tag 54 (Amount) หรือไม่
        if "54" in qr_content:
            print("✅ Tag 54 (Amount) found")
        else:
            print("❌ Tag 54 (Amount) NOT found")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_simple_tag29()
    test_simple_tag30()
    test_with_amount()
    
    print("\n" + "=" * 80)
    print("Test completed!")
    print("=" * 80)
    print("\n💡 Tips:")
    print("1. ตรวจสอบว่า CRC16 ตรงกันหรือไม่")
    print("2. ตรวจสอบโครงสร้าง payload ว่าถูกต้องหรือไม่")
    print("3. ลองสแกน QR Code ด้วยแอปธนาคารและดู error message")
    print("4. เปรียบเทียบกับ QR Code จากเว็บไซต์ promptpay.pro")

