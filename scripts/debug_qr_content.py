"""
Debug script สำหรับตรวจสอบ QR Code Content ที่สร้างขึ้น
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

def debug_qr_content():
    """Debug QR Code Content"""
    
    print("=" * 80)
    print("Debug PromptPay QR Code Content")
    print("=" * 80)
    
    # Test Tag30 - Bill Payment
    print("\n" + "=" * 80)
    print("Tag30 - Bill Payment")
    print("=" * 80)
    
    try:
        qr_content = generate_promptpay_qr_content(
            biller_id="123456789012399",
            ref1="1",
            ref2="5",
            ref3="TEST",
            amount=90.00
        )
        
        print(f"\nQR Content String:")
        print(f"{qr_content}")
        print(f"\nLength: {len(qr_content)} characters")
        
        # แสดงแต่ละ tag
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
                except:
                    print(f"  Error parsing at position {i}")
                    break
            else:
                break
        
        # ตรวจสอบ CRC16
        payload_without_crc = qr_content[:-4]  # ลบ tag 63 ออก
        crc_from_qr = qr_content[-4:]  # เอา CRC จาก tag 63
        
        # คำนวณ CRC16 ใหม่
        payload_bytes = payload_without_crc.encode('utf-8')
        calculated_crc = calculate_crc16(payload_bytes, use_ccitt=False)
        calculated_crc_str = f"{calculated_crc:04X}"
        
        print(f"\nCRC16 Check:")
        print(f"  CRC in QR: {crc_from_qr}")
        print(f"  Calculated CRC: {calculated_crc_str}")
        print(f"  Match: {'✅' if crc_from_qr == calculated_crc_str else '❌'}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test Tag29 - Credit Transfer
    print("\n" + "=" * 80)
    print("Tag29 - Credit Transfer")
    print("=" * 80)
    
    try:
        qr_content = generate_promptpay_credit_transfer_content(
            mobile_number="0812345678",
            amount=90.00
        )
        
        print(f"\nQR Content String:")
        print(f"{qr_content}")
        print(f"\nLength: {len(qr_content)} characters")
        
        # แสดงแต่ละ tag
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
                except:
                    print(f"  Error parsing at position {i}")
                    break
            else:
                break
        
        # ตรวจสอบ CRC16
        payload_without_crc = qr_content[:-4]  # ลบ tag 63 ออก
        crc_from_qr = qr_content[-4:]  # เอา CRC จาก tag 63
        
        # คำนวณ CRC16 ใหม่
        payload_bytes = payload_without_crc.encode('utf-8')
        calculated_crc = calculate_crc16(payload_bytes, use_ccitt=False)
        calculated_crc_str = f"{calculated_crc:04X}"
        
        print(f"\nCRC16 Check:")
        print(f"  CRC in QR: {crc_from_qr}")
        print(f"  Calculated CRC: {calculated_crc_str}")
        print(f"  Match: {'✅' if crc_from_qr == calculated_crc_str else '❌'}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    debug_qr_content()

