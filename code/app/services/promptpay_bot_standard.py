"""
PromptPay QR Code Generator ตามมาตรฐาน BOT
สร้าง QR Code ตามมาตรฐานการรับชำระเงินด้วย QR ของธนาคารแห่งประเทศไทย
- แบบ 362 ตัวอักษร (แบบเต็ม)
- แบบ 62 ตัวอักษร (แบบสั้น)
- Tag29: Credit Transfer
- Tag30: Bill Payment

อ้างอิง: https://www.bot.or.th/content/dam/bot/fipcs/documents/FPG/2562/ThaiPDF/25620084.pdf
"""
import qrcode
from io import BytesIO
import base64
from typing import Optional
from app.services.promptpay import (
    calculate_crc16,
    format_tag
)


def generate_bot_standard_qr_362(
    biller_id: str,
    ref1: str,
    ref2: Optional[str] = None,
    ref3: Optional[str] = None,
    amount: Optional[float] = None,
    # ข้อมูลผู้ซื้อ (ตามตารางที่ 1)
    buyer_name: Optional[str] = None,
    buyer_address: Optional[str] = None,
    buyer_city: Optional[str] = None,
    buyer_province: Optional[str] = None,
    buyer_postcode: Optional[str] = None,
    buyer_country: Optional[str] = None,
    # Type of Income (รหัสประเภทเงินได้พึงประเมิน)
    type_of_income: Optional[str] = None
) -> str:
    """
    สร้าง PromptPay QR Code Content แบบ 362 ตัวอักษร (แบบเต็ม)
    ตามมาตรฐาน BOT ตารางที่ 1
    
    Args:
        biller_id: เลขประจำตัวผู้เสียภาษี + suffix 2 หลัก (15 หลัก)
        ref1: รหัสอ้างอิง 1 (20 หลัก)
        ref2: รหัสอ้างอิง 2 (25 หลัก) - optional
        ref3: รหัสอ้างอิง 3 (27 หลัก) - optional
        amount: จำนวนเงิน - optional
        buyer_name: ชื่อผู้ซื้อ (30 หลัก) - optional
        buyer_address: ที่อยู่ผู้ซื้อ (70 หลัก) - optional
        buyer_city: ชื่อตำบล (30 หลัก) - optional
        buyer_province: ชื่ออำเภอ (30 หลัก) - optional
        buyer_postcode: รหัสไปรษณีย์ (5 หลัก) - optional
        buyer_country: ชื่อประเทศ (30 หลัก) - optional
        type_of_income: รหัสประเภทเงินได้พึงประเมิน (3 หลัก) - optional
    
    Returns:
        QR Code content string (362 ตัวอักษร)
    """
    # Payload Format Indicator
    payload = format_tag("00", "01")
    
    # Point of Initiation Method
    if amount is not None and amount > 0:
        payload += format_tag("01", "12")  # Dynamic
    else:
        payload += format_tag("01", "11")  # Static
    
    # Merchant Account Information (Tag30 - Bill Payment)
    merchant_info = format_tag("00", "A000000677010111")  # PromptPay AID
    
    # Biller ID - 15 หลัก
    biller_id_clean = ''.join(filter(str.isdigit, str(biller_id)))
    if not biller_id_clean:
        raise ValueError("Biller ID must contain at least one digit")
    if len(biller_id_clean) < 15:
        biller_id_clean = biller_id_clean.zfill(15)
    elif len(biller_id_clean) > 15:
        biller_id_clean = biller_id_clean[:15]
    
    merchant_info += format_tag("01", biller_id_clean)
    
    # Reference 1 (Required) - 20 หลัก
    if not ref1:
        raise ValueError("Reference 1 (ref1) is required")
    ref1_clean = str(ref1)[:20]
    merchant_info += format_tag("02", ref1_clean)
    
    # Reference 2 (Optional) - 25 หลัก
    if ref2:
        ref2_clean = str(ref2)[:25]
        merchant_info += format_tag("03", ref2_clean)
    
    # Reference 3 (Optional) - 27 หลัก
    if ref3:
        ref3_clean = str(ref3)[:27]
        merchant_info += format_tag("04", ref3_clean)
    
    payload += format_tag("30", merchant_info)
    
    # Transaction Currency (THB = 764)
    payload += format_tag("53", "764")
    
    # Transaction Amount (Optional)
    if amount is not None:
        amount_float = float(amount)
        if amount_float < 0:
            raise ValueError("Amount cannot be negative")
        if amount_float > 0:
            amount_str = f"{amount_float:.2f}"
            payload += format_tag("54", amount_str)
    
    # Country Code (TH = 764)
    payload += format_tag("58", "TH")
    
    # Additional Data Field Template (Tag62) - สำหรับข้อมูลเพิ่มเติม
    # ตามมาตรฐาน BOT ตารางที่ 1
    additional_data = ""
    
    # Field 1: Buyer Name (30 หลัก)
    if buyer_name:
        buyer_name_clean = str(buyer_name)[:30]
        additional_data += buyer_name_clean + "\r"  # CR (Carriage Return)
    
    # Field 2: Buyer Address (70 หลัก)
    if buyer_address:
        buyer_address_clean = str(buyer_address)[:70]
        additional_data += buyer_address_clean + "\r"
    
    # Field 3: City Name (30 หลัก)
    if buyer_city:
        buyer_city_clean = str(buyer_city)[:30]
        additional_data += buyer_city_clean + "\r"
    
    # Field 4: Province Name (30 หลัก)
    if buyer_province:
        buyer_province_clean = str(buyer_province)[:30]
        additional_data += buyer_province_clean + "\r"
    
    # Field 5: Post Code (5 หลัก)
    if buyer_postcode:
        buyer_postcode_clean = str(buyer_postcode)[:5]
        additional_data += buyer_postcode_clean + "\r"
    
    # Field 6: Country Name (30 หลัก)
    if buyer_country:
        buyer_country_clean = str(buyer_country)[:30]
        additional_data += buyer_country_clean + "\r"
    
    # Field 7: Type of Income (3 หลัก) - รหัสประเภทเงินได้พึงประเมิน
    if type_of_income:
        type_of_income_clean = str(type_of_income)[:3]
        additional_data += type_of_income_clean + "\r"
    
    # เพิ่ม Tag62 ถ้ามีข้อมูลเพิ่มเติม
    if additional_data:
        payload += format_tag("62", additional_data)
    
    # คำนวณ CRC16
    payload_bytes = payload.encode('utf-8')
    crc = calculate_crc16(payload_bytes, use_ccitt=False)
    crc_str = f"{crc:04X}"
    
    # เพิ่ม CRC16 tag (Tag 63)
    payload += format_tag("63", crc_str)
    
    return payload


def generate_bot_standard_qr_62(
    biller_id: str,
    ref1: str,
    ref2: Optional[str] = None,
    ref3: Optional[str] = None,
    amount: Optional[float] = None
) -> str:
    """
    สร้าง PromptPay QR Code Content แบบ 62 ตัวอักษร (แบบสั้น)
    ตามมาตรฐาน BOT
    
    Args:
        biller_id: เลขประจำตัวผู้เสียภาษี + suffix 2 หลัก (15 หลัก)
        ref1: รหัสอ้างอิง 1 (20 หลัก)
        ref2: รหัสอ้างอิง 2 (25 หลัก) - optional
        ref3: รหัสอ้างอิง 3 (27 หลัก) - optional
        amount: จำนวนเงิน - optional
    
    Returns:
        QR Code content string (62 ตัวอักษร)
    """
    # Payload Format Indicator
    payload = format_tag("00", "01")
    
    # Point of Initiation Method
    if amount is not None and amount > 0:
        payload += format_tag("01", "12")  # Dynamic
    else:
        payload += format_tag("01", "11")  # Static
    
    # Merchant Account Information (Tag30 - Bill Payment)
    merchant_info = format_tag("00", "A000000677010111")  # PromptPay AID
    
    # Biller ID - 15 หลัก
    biller_id_clean = ''.join(filter(str.isdigit, str(biller_id)))
    if not biller_id_clean:
        raise ValueError("Biller ID must contain at least one digit")
    if len(biller_id_clean) < 15:
        biller_id_clean = biller_id_clean.zfill(15)
    elif len(biller_id_clean) > 15:
        biller_id_clean = biller_id_clean[:15]
    
    merchant_info += format_tag("01", biller_id_clean)
    
    # Reference 1 (Required) - 20 หลัก
    if not ref1:
        raise ValueError("Reference 1 (ref1) is required")
    ref1_clean = str(ref1)[:20]
    merchant_info += format_tag("02", ref1_clean)
    
    # Reference 2 (Optional) - 25 หลัก
    if ref2:
        ref2_clean = str(ref2)[:25]
        merchant_info += format_tag("03", ref2_clean)
    
    # Reference 3 (Optional) - 27 หลัก
    if ref3:
        ref3_clean = str(ref3)[:27]
        merchant_info += format_tag("04", ref3_clean)
    
    payload += format_tag("30", merchant_info)
    
    # Transaction Currency (THB = 764)
    payload += format_tag("53", "764")
    
    # Transaction Amount (Optional)
    if amount is not None:
        amount_float = float(amount)
        if amount_float < 0:
            raise ValueError("Amount cannot be negative")
        if amount_float > 0:
            amount_str = f"{amount_float:.2f}"
            payload += format_tag("54", amount_str)
    
    # Country Code (TH = 764)
    payload += format_tag("58", "TH")
    
    # คำนวณ CRC16
    payload_bytes = payload.encode('utf-8')
    crc = calculate_crc16(payload_bytes, use_ccitt=False)
    crc_str = f"{crc:04X}"
    
    # เพิ่ม CRC16 tag (Tag 63)
    payload += format_tag("63", crc_str)
    
    return payload


def generate_bot_qr_image(
    qr_content: str,
    size: int = 300
) -> str:
    """
    สร้าง QR Code Image จาก content และแปลงเป็น Base64
    
    Args:
        qr_content: QR Code content string
        size: ขนาด QR Code (pixels)
    
    Returns:
        Base64 encoded image string (data URI format)
    """
    # สร้าง QR Code image
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_content)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img = img.resize((size, size))
    
    # Convert to base64
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return f"data:image/png;base64,{img_str}"

