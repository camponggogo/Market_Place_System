"""
Test script สำหรับตรวจสอบ Tag30 ที่มี amount 14.81
"""
import sys
from pathlib import Path

root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from app.services.promptpay import (
    generate_promptpay_qr_content,
    calculate_crc16,
    format_tag,
    finalize_with_crc
)

def parse_payload(payload: str):
    """Parse payload และแสดงแต่ละ tag"""
    print(f"\nFull payload: {payload}")
    print(f"Length: {len(payload)} characters\n")
    print("Tags breakdown:")
    i = 0
    while i < len(payload):
        if i + 4 <= len(payload):
            tag = payload[i:i+2]
            length_str = payload[i+2:i+4]
            try:
                length = int(length_str)
                value = payload[i+4:i+4+length]
                print(f"  Tag {tag}: Length={length_str} ({length}), Value='{value}'")
                i += 4 + length
            except Exception as e:
                print(f"  Error parsing at position {i}: {e}")
                break
        else:
            break

def test_tag30_with_amount():
    """ทดสอบ Tag30 พร้อม amount 14.81"""
    print("=" * 80)
    print("Test Tag30 - With Amount 14.81")
    print("=" * 80)
    
    biller_id = "0000000000000"
    ref1 = "0000001"
    amount = 14.81
    
    # Test 1: Minimal mode (ไม่มี EMV tags)
    print("\n1. Minimal mode (include_emv_tags=False):")
    try:
        qr_content_minimal = generate_promptpay_qr_content(
            biller_id=biller_id,
            ref1=ref1,
            amount=amount,
            include_emv_tags=False
        )
        parse_payload(qr_content_minimal)
        
        # ตรวจสอบ CRC16
        crc_tag_pos = qr_content_minimal.rfind("63")
        if crc_tag_pos != -1:
            payload_without_crc = qr_content_minimal[:crc_tag_pos]
            crc_length_str = qr_content_minimal[crc_tag_pos+2:crc_tag_pos+4]
            crc_length = int(crc_length_str)
            crc_from_qr = qr_content_minimal[crc_tag_pos+4:crc_tag_pos+4+crc_length]
            
            # คำนวณ CRC16 ใหม่
            payload_for_crc = f"{payload_without_crc}6304"
            calculated_crc = calculate_crc16(payload_for_crc.encode('utf-8'), use_ccitt=True)
            
            print(f"\nCRC16 Check:")
            print(f"  CRC in QR: {crc_from_qr}")
            print(f"  Calculated CRC: {calculated_crc:04X}")
            print(f"  Match: {'✅' if crc_from_qr == f'{calculated_crc:04X}' else '❌'}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: EMV mode (มี EMV tags)
    print("\n" + "=" * 80)
    print("2. EMV mode (include_emv_tags=True):")
    try:
        qr_content_emv = generate_promptpay_qr_content(
            biller_id=biller_id,
            ref1=ref1,
            amount=amount,
            include_emv_tags=True
        )
        parse_payload(qr_content_emv)
        
        # ตรวจสอบ CRC16
        crc_tag_pos = qr_content_emv.rfind("63")
        if crc_tag_pos != -1:
            payload_without_crc = qr_content_emv[:crc_tag_pos]
            crc_length_str = qr_content_emv[crc_tag_pos+2:crc_tag_pos+4]
            crc_length = int(crc_length_str)
            crc_from_qr = qr_content_emv[crc_tag_pos+4:crc_tag_pos+4+crc_length]
            
            # คำนวณ CRC16 ใหม่
            payload_for_crc = f"{payload_without_crc}6304"
            calculated_crc = calculate_crc16(payload_for_crc.encode('utf-8'), use_ccitt=True)
            
            print(f"\nCRC16 Check:")
            print(f"  CRC in QR: {crc_from_qr}")
            print(f"  Calculated CRC: {calculated_crc:04X}")
            print(f"  Match: {'✅' if crc_from_qr == f'{calculated_crc:04X}' else '❌'}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: เปรียบเทียบกับแบบไม่มี amount
    print("\n" + "=" * 80)
    print("3. Compare with NO amount (should scan OK):")
    try:
        qr_content_no_amount = generate_promptpay_qr_content(
            biller_id=biller_id,
            ref1=ref1,
            amount=None,
            include_emv_tags=False
        )
        print(f"\nPayload (no amount): {qr_content_no_amount}")
        print(f"Length: {len(qr_content_no_amount)} characters")
        
        # เปรียบเทียบความแตกต่าง
        print(f"\nDifferences:")
        print(f"  With amount length: {len(qr_content_minimal)}")
        print(f"  No amount length: {len(qr_content_no_amount)}")
        print(f"  Difference: {len(qr_content_minimal) - len(qr_content_no_amount)} chars")
        
        # ตรวจสอบว่า Tag 54 (Amount) ถูกต้องหรือไม่
        if "54" in qr_content_minimal:
            tag54_pos = qr_content_minimal.find("54")
            if tag54_pos != -1:
                tag54_length_str = qr_content_minimal[tag54_pos+2:tag54_pos+4]
                tag54_length = int(tag54_length_str)
                tag54_value = qr_content_minimal[tag54_pos+4:tag54_pos+4+tag54_length]
                print(f"\nTag 54 (Amount) details:")
                print(f"  Position: {tag54_pos}")
                print(f"  Length: {tag54_length_str} ({tag54_length})")
                print(f"  Value: '{tag54_value}'")
                print(f"  Expected: '14.81'")
                print(f"  Match: {'✅' if tag54_value == '14.81' else '❌'}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_tag30_with_amount()

