# คู่มือการติดตั้งและใช้งานระบบ Food Court Management System

## ข้อกำหนดระบบ

### 1. ระบบ Customer Interface & Balance Monitoring

#### 1.1 ตรวจสอบยอดเงินผ่าน QR Code
- ลูกค้าสามารถ Scan QR Code จากบัตรหรือใบเสร็จเพื่อเช็คยอดคงเหลือ
- เข้าถึงได้ผ่าน: `http://localhost:8000/static/index.html`
- API Endpoint: `POST /api/customers/check-balance`

#### 1.2 ระบบแจ้งเตือนคืนเงินอัตโนมัติ (Configurable E-Money Guard)

**การตั้งค่าใน config.ini:**
```ini
[E_MONEY]
HAS_E_MONEY_LICENSE=False          # ตั้งค่าเป็น True ถ้ามีใบอนุญาต e-Money
AUTO_REFUND_ENABLED=True           # เปิด/ปิดการแจ้งเตือนอัตโนมัติ
REFUND_NOTIFICATION_TIME=23:00     # เวลาที่จะส่งการแจ้งเตือน
DAILY_BALANCE_RESET=True           # รีเซ็ตยอดเงินทุกสิ้นวัน
```

**การทำงาน:**
- **โหมดไม่มีใบอนุญาต e-Money**: ระบบจะแจ้งเตือนลูกค้าเมื่อจบวัน เพื่อให้เลือกวิธีรับเงินคืน (เงินสด/PromptPay) และเคลียร์ยอดเป็น 0 ทุกสิ้นวัน
- **โหมดมีใบอนุญาต e-Money**: ปิดการแจ้งเตือนและปล่อยให้ยอดคงเหลือค้างในระบบ

#### 1.3 Self-Service Refund
- ลูกค้าสามารถเลือกวิธีรับเงินคืนได้เองผ่านหน้าจอ Mobile
- วิธี: เงินสด (รับที่เคาน์เตอร์) หรือ PromptPay (โอนคืนอัตโนมัติ)
- API Endpoint: `POST /api/customers/refund`

### 2. ระบบ Crypto Infrastructure (P2P Contract Model)

#### 2.1 E-Contract สำหรับร้านค้า
- ร้านค้าต้องยอมรับสัญญา P2P ก่อนเปิดใช้งาน Crypto Payment
- เข้าถึงสัญญาได้ที่: `http://localhost:8000/contracts/p2p_contract_template.html?store_id={store_id}`
- API Endpoint: `POST /api/crypto/stores/accept-contract`

#### 2.2 Transaction Monitoring
- ระบบดึงข้อมูล Transaction Status จาก Blockchain Explorer
- แสดงผลที่หน้า POS ของร้านค้า
- API Endpoint: `GET /api/crypto/transactions/{tx_hash}/status`

#### 2.3 Fee Model
- **Transaction Fee**: เก็บค่า Service Fee เป็นรายรายการ (ตั้งค่าใน config.ini)
- **Flat Fee**: เก็บแบบเหมาจ่ายรายเดือน (ตั้งค่าใน config.ini)

### 3. ระบบรายงานและบัญชี

#### 3.1 Separation of Funds Report
- แยกยอดเงินสด/โอน (Revenue) ออกจากยอด Crypto Status (Information Only)
- API Endpoint: `GET /api/reports/separation-of-funds`

#### 3.2 Automated WHT
- คำนวณภาษีหัก ณ ที่จ่าย 3% อัตโนมัติ
- API Endpoint: `GET /api/reports/wht-calculation`

#### 3.3 Sales Tax Report
- รายงานภาษีขายตามรูปแบบที่สรรพากรกำหนด
- API Endpoint: `GET /api/reports/sales-tax`

### 4. ระบบ POS Compliance

#### 4.1 ใบกำกับภาษีอย่างย่อ (ภ.พ. 89)
- ออกใบกำกับภาษีอัตโนมัติเมื่อมีการทำรายการ
- API Endpoint: `POST /api/tax/invoices/{transaction_id}`

#### 4.2 E-Tax Invoice Integration
- ส่งข้อมูลใบกำกับภาษีไปยัง Provider โดยตรง
- API Endpoint: `POST /api/tax/invoices/{invoice_id}/send-e-tax`

## การติดตั้ง

### 1. ติดตั้ง Dependencies
```bash
pip install -r requirements.txt
```

### 2. ตั้งค่า Database
- สร้าง MariaDB Database
- สร้าง database ชื่อ `foodcourt` (หรือชื่ออื่นตามที่ต้องการ)
- แก้ไข `config.ini` ตามข้อมูล Database ของคุณ
- Default settings: user=root, password=123456, port=3306

### 3. สร้าง Database Tables
```bash
python -c "from app.database import engine, Base; Base.metadata.create_all(bind=engine)"
```

### 4. ตั้งค่า Config
แก้ไขไฟล์ `config.ini` ตามสภาพแวดล้อมของคุณ:
- Database connection
- E-Money license status
- Crypto settings
- Tax information
- Notification settings (LINE OA)

### 5. รันระบบ
```bash
uvicorn main:app --reload
```

### 6. รัน Scheduler (สำหรับ Daily Reset และ Notifications)
```bash
python app/scheduler.py
```

หรือใช้ systemd/cron job:
```bash
# Crontab example
0 0 * * * cd /path/to/project && python -c "from app.scheduler import daily_balance_reset; daily_balance_reset()"
```

## การใช้งาน

### สำหรับลูกค้า
1. เข้าใช้งาน: `http://localhost:8000/static/index.html`
2. สแกน QR Code หรือกรอกรหัสลูกค้า
3. ตรวจสอบยอดเงินคงเหลือ
4. ขอคืนเงิน (ถ้ามียอดเงิน)

### สำหรับร้านค้า
1. เข้าใช้งาน Dashboard: `http://localhost:8000/static/store_dashboard.html`
2. ยอมรับสัญญา P2P (ถ้าต้องการรับ Crypto Payment)
3. ตรวจสอบสถานะ Crypto Transactions

### สำหรับ Admin
1. ดูรายงาน: `/api/reports/sales-tax`, `/api/reports/separation-of-funds`
2. จัดการคำขอคืนเงิน: `/api/refunds/pending`
3. ประมวลผลการคืนเงิน: `POST /api/refunds/{refund_request_id}/process`

## API Documentation
เข้าถึงได้ที่: `http://localhost:8000/docs` (Swagger UI)

## หมายเหตุสำคัญ

1. **E-Money License**: ต้องตั้งค่า `HAS_E_MONEY_LICENSE` ใน config.ini ให้ถูกต้อง
2. **Crypto Transactions**: ระบบจะแสดงข้อมูลจาก Blockchain Explorer เท่านั้น ไม่รับผิดชอบต่อการโอนเงิน
3. **Tax Compliance**: ระบบออกใบกำกับภาษีเฉพาะค่าบริการ ไม่รวมมูลค่า Crypto
4. **Audit Trail**: ระบบบันทึก Audit Log ทุกการเปลี่ยนแปลงข้อมูล

## การขออนุญาต POS กับกรมสรรพากร

### เอกสารที่ต้องเตรียม:
1. แผนผังการติดตั้งเครื่อง (Layout) ใน Food Court
2. ตัวอย่างใบกำกับภาษีอย่างย่อที่ออกจากระบบ
3. คู่มือการใช้งานซอฟต์แวร์ POS
4. หนังสือรับรองบริษัทและภ.พ. 20

### การแจ้งใช้:
- ใช้แบบฟอร์ม ภ.พ. 06
- ระบุยี่ห้อ รุ่น และหมายเลขผลิตภัณฑ์ (Serial Number)
- ระบุชื่อซอฟต์แวร์ที่ใช้

