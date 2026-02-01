"""
PromptPay QR Code Generator
สร้าง QR Code สำหรับ PromptPay ตามมาตรฐาน Thai QR Payment
- Tag29: Credit Transfer (สำหรับบุคคลธรรมดา)
- Tag30: Bill Payment (สำหรับธุรกิจ)
"""
import qrcode
from io import BytesIO
import base64
from typing import Optional


def calculate_crc16_ccitt(data: bytes) -> int:
    """
    คำนวณ CRC16-CCITT สำหรับ PromptPay QR Code
    ตามมาตรฐาน EMV QR Code (Thai QR Payment)
    
    มาตรฐาน: EMV QR Code Specification
    Polynomial: 0x1021
    Initial value: 0xFFFF
    
    อ้างอิง: 
    - มาตรฐานการรับชำระเงินด้วย QR ของธนาคารแห่งประเทศไทย
    - https://medium.com/i-gear-geek/build-promptpay-qr-step-by-step-e67ddacf36af
    """
    crc = 0xFFFF
    polynomial = 0x1021
    
    for byte_val in data:
        # XOR with byte (shift left 8 bits)
        crc ^= (byte_val << 8) & 0xFFFF
        
        # Process 8 bits
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ polynomial) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    
    return crc & 0xFFFF


def calculate_crc16_custom(data: bytes) -> int:
    """
    คำนวณ CRC16 แบบ Custom
    อ้างอิงจาก: https://stackoverflow.com/questions/13209364/convert-c-crc16-to-java-crc16/13209435
    
    Algorithm:
    - Initial value: 0xFFFF
    - For each byte:
      1. Swap bytes: (crc >> 8) | (crc << 8)
      2. XOR with byte
      3. XOR with (crc & 0xFF) >> 4
      4. XOR with crc << 12
      5. XOR with (crc & 0xFF) << 5
    """
    crc = 0xFFFF
    
    for byte_val in data:
        # Swap bytes: (crc >> 8) | (crc << 8)
        crc = ((crc >> 8) | (crc << 8)) & 0xFFFF
        
        # XOR with byte (convert to unsigned)
        crc ^= (byte_val & 0xFF)
        
        # XOR with ((crc & 0xFF) >> 4)
        crc ^= ((crc & 0xFF) >> 4)
        
        # XOR with (crc << 12)
        crc ^= (crc << 12) & 0xFFFF
        
        # XOR with ((crc & 0xFF) << 5)
        crc ^= ((crc & 0xFF) << 5) & 0xFFFF
    
    # Ensure result is 16-bit
    crc &= 0xFFFF
    
    return crc


def calculate_crc16(data: bytes, use_ccitt: bool = True) -> int:
    """
    คำนวณ CRC16 สำหรับ PromptPay QR Code
    
    Args:
        data: ข้อมูลที่ต้องการคำนวณ CRC16
        use_ccitt: True = ใช้ CRC16-CCITT (มาตรฐาน EMV - default), False = ใช้ Custom algorithm
    
    Returns:
        CRC16 checksum (16-bit)
    
    หมายเหตุ:
    - Default ใช้ CRC16-CCITT (polynomial 0x1021) ตามมาตรฐาน EMV และบทความ Medium
    - อ้างอิง: https://medium.com/i-gear-geek/build-promptpay-qr-step-by-step-e67ddacf36af
    - สามารถเปลี่ยนเป็น Custom algorithm ได้โดยตั้ง use_ccitt=False
    """
    if use_ccitt:
        return calculate_crc16_ccitt(data)
    else:
        return calculate_crc16_custom(data)


def format_tag(tag: str, value: str) -> str:
    """
    จัดรูปแบบ Tag สำหรับ PromptPay QR Code
    """
    tag_str = tag.zfill(2)
    # EMV TLV length ต้องนับเป็นจำนวน "bytes" ของค่าที่ encode แล้ว (โดยทั่วไปเป็น UTF-8)
    # ถ้าใช้ len(str) จะผิดทันทีเมื่อมีภาษาไทย/อักขระ multi-byte ทำให้สแกนไม่ผ่าน
    length = len(value.encode("utf-8"))
    length_str = str(length).zfill(2)
    return f"{tag_str}{length_str}{value}"


def finalize_with_crc(payload_without_crc_tag: str, use_ccitt: bool = True) -> str:
    """
    เติม CRC16 (Tag63) ตามมาตรฐาน EMV

    หมายเหตุสำคัญ:
    - CRC16 ต้องคำนวณบน payload ที่ "เติม 6304" (Tag 63 + Length 04) แล้ว
      แต่ยังไม่ใส่ค่า CRC (4 chars) เข้าไป
    - แล้วจึงค่อย append ค่า CRC 4 ตัวอักษร (HEX) ต่อท้าย
    """
    payload_for_crc = f"{payload_without_crc_tag}6304"
    crc = calculate_crc16(payload_for_crc.encode("utf-8"), use_ccitt=use_ccitt)
    return f"{payload_for_crc}{crc:04X}"


def generate_promptpay_qr_content(
    biller_id: str,
    ref1: str,
    ref2: Optional[str] = None,
    ref3: Optional[str] = None,
    amount: Optional[float] = None,
    merchant_name: str = "NA",
    merchant_city: str = "BANGKOK",
    include_emv_tags: bool = True,
) -> str:
    """
    สร้าง PromptPay QR Code Content (Tag30 - Bill Payment)
    
    Args:
        biller_id: เลขประจำตัวผู้เสียภาษี + suffix 2 หลัก (เช่น "000000000000099")
        ref1: รหัสอ้างอิง 1 (เช่น store.id)
        ref2: รหัสอ้างอิง 2 (เช่น menu.id) - optional
        ref3: รหัสอ้างอิง 3 (เช่น remark) - optional
        amount: จำนวนเงิน - optional
    
    Returns:
        QR Code content string
    """
    # Payload Format Indicator
    payload = format_tag("00", "01")
    
    # Point of Initiation Method (11 = static, 12 = dynamic)
    # ใช้ "12" (dynamic) ถ้ามี amount, "11" (static) ถ้าไม่มี amount
    if amount is not None and amount > 0:
        payload += format_tag("01", "12")  # Dynamic
    else:
        payload += format_tag("01", "11")  # Static
    
    # Merchant Account Information (Tag30 - Bill Payment)
    # หมายเหตุ: Bill Payment ใช้ PromptPay AID คนละตัวกับ Credit Transfer
    # - Credit Transfer (Tag29): A000000677010111
    # - Bill Payment (Tag30):    A000000677010112
    merchant_info = format_tag("00", "A000000677010112")  # PromptPay Bill Payment AID
    
    # Biller ID - ต้องเป็นตัวเลข 15 หลัก
    biller_id_clean = ''.join(filter(str.isdigit, str(biller_id)))
    if not biller_id_clean:
        raise ValueError("Biller ID must contain at least one digit")
    if len(biller_id_clean) < 15:
        biller_id_clean = biller_id_clean.zfill(15)
    elif len(biller_id_clean) > 15:
        biller_id_clean = biller_id_clean[:15]
    
    merchant_info += format_tag("01", biller_id_clean)
    
    # Reference 1 (Required) - ต้องไม่ว่าง
    if not ref1:
        raise ValueError("Reference 1 (ref1) is required")
    ref1_clean = str(ref1)[:20]
    merchant_info += format_tag("02", ref1_clean)
    
    # Reference 2 (Optional)
    if ref2:
        ref2_clean = str(ref2)[:25]
        merchant_info += format_tag("03", ref2_clean)
    
    # Reference 3 (Optional)
    if ref3:
        ref3_clean = str(ref3)[:27]
        merchant_info += format_tag("04", ref3_clean)
    
    payload += format_tag("30", merchant_info)

    if include_emv_tags:
        # Merchant Category Code (required in EMV MPM)
        payload += format_tag("52", "0000")

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

        # Country Code
        payload += format_tag("58", "TH")
    else:
        # Minimal order (ให้ตรงกับมาตรฐาน EMV และ promptpay-qr):
        # ตามมาตรฐาน EMV: 53 (Currency) -> 54 (Amount) -> 58 (Country)
        payload += format_tag("53", "764")
        if amount is not None:
            amount_float = float(amount)
            if amount_float < 0:
                raise ValueError("Amount cannot be negative")
            if amount_float > 0:
                payload += format_tag("54", f"{amount_float:.2f}")
        payload += format_tag("58", "TH")

    if include_emv_tags:
        # Merchant Name / City (required in EMV MPM)
        merchant_name_clean = str(merchant_name)[:25] if merchant_name else "NA"
        merchant_city_clean = str(merchant_city)[:15] if merchant_city else "BANGKOK"
        payload += format_tag("59", merchant_name_clean)
        payload += format_tag("60", merchant_city_clean)

    return finalize_with_crc(payload, use_ccitt=True)


def generate_promptpay_qr_image(
    biller_id: str,
    ref1: str,
    ref2: Optional[str] = None,
    ref3: Optional[str] = None,
    amount: Optional[float] = None,
    merchant_name: str = "NA",
    merchant_city: str = "BANGKOK",
    include_emv_tags: bool = True,
    size: int = 300
) -> str:
    """
    สร้าง PromptPay QR Code Image และแปลงเป็น Base64
    
    Args:
        biller_id: เลขประจำตัวผู้เสียภาษี + suffix 2 หลัก
        ref1: รหัสอ้างอิง 1
        ref2: รหัสอ้างอิง 2 - optional
        ref3: รหัสอ้างอิง 3 - optional
        amount: จำนวนเงิน - optional
        size: ขนาด QR Code (pixels)
    
    Returns:
        Base64 encoded image string (data URI format)
    """
    # สร้าง QR Code content
    qr_content = generate_promptpay_qr_content(
        biller_id=biller_id,
        ref1=ref1,
        ref2=ref2,
        ref3=ref3,
        amount=amount,
        merchant_name=merchant_name,
        merchant_city=merchant_city,
        include_emv_tags=include_emv_tags,
    )
    
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


def generate_promptpay_credit_transfer_content(
    mobile_number: Optional[str] = None,
    national_id: Optional[str] = None,
    e_wallet_id: Optional[str] = None,
    amount: Optional[float] = None,
    merchant_name: str = "NA",
    merchant_city: str = "BANGKOK",
    include_emv_tags: bool = True,
) -> str:
    """
    สร้าง PromptPay QR Code Content (Tag29 - Credit Transfer)
    สำหรับบุคคลธรรมดารับโอนเงิน
    
    Args:
        mobile_number: เบอร์โทรศัพท์ (10 หลัก) - เช่น "0812345678"
        national_id: เลขประจำตัวประชาชน (13 หลัก) - เช่น "1234567890123"
        e_wallet_id: E-Wallet ID (15 หลัก) - เช่น "000000000000000"
        amount: จำนวนเงิน - optional
    
    Returns:
        QR Code content string
    """
    # ตรวจสอบว่ามีข้อมูลอย่างน้อย 1 อย่าง
    if not mobile_number and not national_id and not e_wallet_id:
        raise ValueError("At least one of mobile_number, national_id, or e_wallet_id is required")
    
    # Payload Format Indicator
    payload = format_tag("00", "01")
    
    # Point of Initiation Method (11 = static, 12 = dynamic)
    if amount is not None and amount > 0:
        payload += format_tag("01", "12")  # Dynamic (มี amount)
    else:
        payload += format_tag("01", "11")  # Static (ไม่มี amount)
    
    # Merchant Account Information (Tag29 - Credit Transfer)
    merchant_info = format_tag("00", "A000000677010111")  # PromptPay AID
    
    # เลือกประเภท ID ที่จะใช้ (ลำดับความสำคัญ: mobile > national_id > e_wallet)
    if mobile_number:
        # Mobile Number - ต้องเป็นตัวเลข 10 หลัก
        mobile_clean = ''.join(filter(str.isdigit, str(mobile_number)))
        if len(mobile_clean) != 10:
            raise ValueError("Mobile number must be 10 digits")
        # แปลงเป็นรูปแบบ +66 (เอา 0 หน้าออก แล้วเติม 0066)
        if mobile_clean.startswith('0'):
            mobile_formatted = "0066" + mobile_clean[1:]
        else:
            mobile_formatted = "0066" + mobile_clean
        merchant_info += format_tag("01", mobile_formatted)
    elif national_id:
        # National ID - ต้องเป็นตัวเลข 13 หลัก
        national_id_clean = ''.join(filter(str.isdigit, str(national_id)))
        if len(national_id_clean) != 13:
            raise ValueError("National ID must be 13 digits")
        # National ID ต้องเติม 000 หน้าสำหรับ Tag29
        national_id_formatted = "000" + national_id_clean
        merchant_info += format_tag("02", national_id_formatted)
    elif e_wallet_id:
        # E-Wallet ID - ต้องเป็นตัวเลข 15 หลัก
        e_wallet_clean = ''.join(filter(str.isdigit, str(e_wallet_id)))
        if len(e_wallet_clean) != 15:
            raise ValueError("E-Wallet ID must be 15 digits")
        merchant_info += format_tag("03", e_wallet_clean)
    
    payload += format_tag("29", merchant_info)

    if include_emv_tags:
        # Merchant Category Code (required in EMV MPM)
        payload += format_tag("52", "0000")

        # Transaction Currency (THB = 764)
        payload += format_tag("53", "764")

        # Transaction Amount (Optional)
        if amount is not None:
            amount_float = float(amount)
            if amount_float < 0:
                raise ValueError("Amount cannot be negative")
            if amount_float > 0:
                payload += format_tag("54", f"{amount_float:.2f}")

        # Country Code
        payload += format_tag("58", "TH")
    else:
        # Minimal order (ให้ตรงกับหลายตัวอย่าง promptpay-qr):
        # ... Merchant Account ... -> 58 -> 53 -> 54 -> CRC
        payload += format_tag("58", "TH")
        payload += format_tag("53", "764")
        if amount is not None:
            amount_float = float(amount)
            if amount_float < 0:
                raise ValueError("Amount cannot be negative")
            if amount_float > 0:
                payload += format_tag("54", f"{amount_float:.2f}")

    if include_emv_tags:
        # Merchant Name / City (required in EMV MPM)
        merchant_name_clean = str(merchant_name)[:25] if merchant_name else "NA"
        merchant_city_clean = str(merchant_city)[:15] if merchant_city else "BANGKOK"
        payload += format_tag("59", merchant_name_clean)
        payload += format_tag("60", merchant_city_clean)

    return finalize_with_crc(payload, use_ccitt=True)


def generate_promptpay_credit_transfer_image(
    mobile_number: Optional[str] = None,
    national_id: Optional[str] = None,
    e_wallet_id: Optional[str] = None,
    amount: Optional[float] = None,
    merchant_name: str = "NA",
    merchant_city: str = "BANGKOK",
    include_emv_tags: bool = True,
    size: int = 300
) -> str:
    """
    สร้าง PromptPay QR Code Image (Tag29 - Credit Transfer) และแปลงเป็น Base64
    
    Args:
        mobile_number: เบอร์โทรศัพท์ (10 หลัก)
        national_id: เลขประจำตัวประชาชน (13 หลัก)
        e_wallet_id: E-Wallet ID (15 หลัก)
        amount: จำนวนเงิน - optional
        size: ขนาด QR Code (pixels)
    
    Returns:
        Base64 encoded image string (data URI format)
    """
    # สร้าง QR Code content
    qr_content = generate_promptpay_credit_transfer_content(
        mobile_number=mobile_number,
        national_id=national_id,
        e_wallet_id=e_wallet_id,
        amount=amount,
        merchant_name=merchant_name,
        merchant_city=merchant_city,
        include_emv_tags=include_emv_tags,
    )
    
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

