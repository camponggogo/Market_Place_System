# Market_Place_System

**ระบบจัดการตลาดนัด Onlinehelp**

ระบบบริหารจัดการ Food Court / ตลาดนัด ที่รองรับการชำระเงินหลากหลายรูปแบบ พร้อมระบบป้องกันข้อจำกัดด้านใบอนุญาต e-Money และการบริหารจัดการความเสี่ยงด้าน Crypto

## คุณสมบัติหลัก

### 1. ระบบ Customer Interface & Balance Monitoring
- ตรวจสอบยอดเงินผ่าน QR Code (Line OA / Web App)
- ระบบแจ้งเตือนคืนเงินอัตโนมัติ (Configurable E-Money Guard)
- Self-Service Refund (เงินสด/PromptPay)

### 2. ระบบ Crypto Infrastructure (P2P Contract Model)
- E-Contract สำหรับร้านค้า
- Transaction Monitoring จาก Blockchain Explorer
- Fee Model (Transaction Fee / Flat Fee)

### 3. ระบบรายงานและบัญชี
- Separation of Funds Report
- Automated WHT (3%)
- E-Tax Invoice Integration

### 4. ระบบ POS Compliance
- ใบกำกับภาษีอย่างย่อ (ภ.พ. 89)
- Auditor Trail
- Sales Tax Report

## การติดตั้ง

```bash
pip install -r requirements.txt
```

## การตั้งค่า

แก้ไขไฟล์ `config.ini` ตามสภาพแวดล้อมของคุณ

## การรัน

```bash
uvicorn main:app --reload
```

