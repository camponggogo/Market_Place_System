# รายละเอียดคุณสมบัติระบบ Food Court Management System

## 1. ระบบ Customer Interface & Balance Monitoring

### 1.1 ตรวจสอบยอดเงินผ่าน QR Code
- **ฟีเจอร์**: ลูกค้าสามารถ Scan QR Code จากบัตรหรือใบเสร็จเพื่อเช็คยอดคงเหลือแบบ Real-time
- **การเข้าถึง**: 
  - Line OA (ต้องเชื่อมต่อ LINE OA API)
  - Web App: `http://localhost:8000/static/index.html`
- **API**: `POST /api/customers/check-balance`

### 1.2 Configurable Refund Engine (ระบบป้องกันการเข้าข่าย e-Money)

#### โหมดไม่มีใบอนุญาต e-Money
- ระบบจะบังคับ Set "Refund Policy" ให้แจ้งเตือนลูกค้า (Push Notification) เมื่อจบวันหรือตามรอบที่ตั้งไว้
- ลูกค้าสามารถเลือก:
  - "รับเงินคืนเป็นเงินสดที่เคาน์เตอร์"
  - "โอนคืนผ่าน PromptPay"
- ระบบจะเคลียร์ยอดเป็น 0 ทุกสิ้นวัน (เพื่อไม่ให้เป็นการรับฝากเงินล่วงหน้าเกินขอบเขตที่กฎหมายกำหนด)

#### โหมดมีใบอนุญาต e-Money
- ผู้ดูแลสามารถปิดระบบแจ้งเตือนคืนเงิน
- ปล่อยให้ยอดคงเหลือค้างในระบบ (Carry over) เพื่อใช้ในครั้งถัดไปได้

### 1.3 Refund Self-Service
- ลูกค้าสามารถเลือกวิธีรับเงินคืนได้เองผ่านหน้าจอ Mobile
- ช่วยลดภาระคิวที่หน้าเคาน์เตอร์
- รองรับ 2 วิธี:
  - เงินสด (ต้องไปรับที่เคาน์เตอร์)
  - PromptPay (โอนคืนอัตโนมัติ)

## 2. ระบบ Crypto Infrastructure (P2P Contract Model)

### 2.1 P2P Agreement Digitization
- ระบบจะมีหน้าจอให้ร้านค้ากดยอมรับ "ข้อตกลงการรับชำระอิสระ"
- ระบุชัดเจนว่าเจ้าของระบบ Food Court เป็นเพียง "ผู้ให้บริการซอฟต์แวร์แสดงผลข้อมูล Blockchain" เท่านั้น
- ร้านค้าต้องยอมรับสัญญาก่อนเปิดใช้งาน Crypto Payment
- เข้าถึงได้ที่: `/contracts/p2p_contract_template.html?store_id={store_id}`

### 2.2 Transaction Monitoring Interface
- ระบบจะดึงข้อมูล Status Transaction จาก Public Block Explorer มาแสดงผลที่หน้า POS ของร้านค้า
- ยืนยันว่าการโอน P2P ของลูกค้าสำเร็จแล้ว
- API: `GET /api/crypto/transactions/{tx_hash}/status`
- Dashboard: `/static/store_dashboard.html`

### 2.3 Fee Model

#### Transaction Fee
- เก็บค่า Service Fee เป็นรายรายการ (เช่น 5-10 บาทต่อครั้ง)
- ในฐานะค่าบริการ API/Node Interface
- ตั้งค่าใน `config.ini`: `TRANSACTION_FEE=5.00`

#### Flat Fee
- เก็บแบบเหมาจ่ายรายเดือนเป็นค่า "Crypto Gateway Information Service"
- ตั้งค่าใน `config.ini`: `MONTHLY_FLAT_FEE=500.00`

### 2.4 Disclaimers
- ระบบจะไม่ออกใบกำกับภาษีในส่วนของมูลค่า Crypto
- จะออกใบกำกับภาษีเฉพาะ "ค่าบริการระบบ" ที่เรียกเก็บจากร้านค้าเท่านั้น

## 3. โครงสร้างรายงานและบัญชี (Legal & Tax Reporting)

### 3.1 Separation of Funds Report
- แยกยอดเงินสด/โอน (Revenue) ออกจากยอด Crypto Status (Information Only) อย่างชัดเจน
- API: `GET /api/reports/separation-of-funds`
- รายงานแสดง:
  - Revenue transactions (Cash, PromptPay, Credit)
  - Crypto information (Information only, not included in revenue)

### 3.2 Automated WHT (Withholding Tax)
- คำนวณภาษีหัก ณ ที่จ่าย 3% อัตโนมัติเมื่อมีการสรุปยอดโอนเงินให้ร้านค้า
- API: `GET /api/reports/wht-calculation?amount={amount}`
- ตั้งค่าใน `config.ini`: `WHT_RATE=0.03`

### 3.3 E-Tax Invoice Integration
- เชื่อมต่อกับ Provider เพื่อส่งข้อมูลใบกำกับภาษีให้สรรพากรโดยตรง
- ลดขั้นตอนการทำเอกสาร
- API: `POST /api/tax/invoices/{invoice_id}/send-e-tax`
- TODO: ต้องเชื่อมต่อกับ E-Tax Invoice Provider จริง (เช่น RD Smart)

## 4. ระบบ POS Compliance

### 4.1 ใบกำกับภาษีอย่างย่อ (ภ.พ. 89)
- ออกใบกำกับภาษีอัตโนมัติเมื่อมีการทำรายการ
- มีรายการครบถ้วน:
  - ชื่อผู้ขาย
  - เลขประจำตัวผู้เสียภาษี
  - เลขที่ใบเสร็จ
  - รายการสินค้า
  - ภาษีมูลค่าเพิ่ม 7%
- API: `POST /api/tax/invoices/{transaction_id}`

### 4.2 Auditor Trail
- ระบบบันทึก Audit Log ทุกการเปลี่ยนแปลงข้อมูล
- Model: `AuditLog` บันทึก:
  - User ID
  - Action
  - Table name
  - Record ID
  - Old values / New values
  - IP Address
  - Timestamp

### 4.3 Sales Tax Report
- รายงานภาษีขายตามรูปแบบที่สรรพากรกำหนด
- API: `GET /api/reports/sales-tax`
- แสดง:
  - สรุปยอดขายแยกตามประเภทการชำระเงิน
  - VAT calculation
  - WHT calculation
  - รายละเอียด transactions

## 5. Scheduled Tasks (Cron Jobs)

### 5.1 Daily Balance Reset
- รีเซ็ตยอดเงินทุกสิ้นวัน (เมื่อไม่มีใบอนุญาต e-Money)
- รันเวลา: 00:00 ทุกวัน
- Script: `app/scheduler.py`

### 5.2 Refund Notifications
- ส่งการแจ้งเตือนคืนเงินให้ลูกค้าที่มียอดเงินคงเหลือ
- รันตามเวลาที่ตั้งไว้ใน config: `REFUND_NOTIFICATION_TIME`
- Default: 23:00

### 5.3 Crypto Transaction Updates
- อัพเดทสถานะ Crypto Transactions จาก Blockchain Explorer
- รันทุก 5 นาที

## 6. API Endpoints Summary

### Customer APIs
- `POST /api/customers/check-balance` - ตรวจสอบยอดเงินผ่าน QR Code
- `GET /api/customers/{customer_id}/balance` - ดึงยอดเงินคงเหลือ
- `POST /api/customers/refund` - สร้างคำขอคืนเงิน
- `GET /api/customers/{customer_id}/refund-requests` - ดึงรายการคำขอคืนเงิน
- `POST /api/customers/generate-qr/{customer_id}` - สร้าง QR Code

### Crypto APIs
- `GET /api/crypto/stores/{store_id}/contract-status` - ตรวจสอบสถานะสัญญา
- `POST /api/crypto/stores/accept-contract` - ยอมรับสัญญา P2P
- `POST /api/crypto/transactions` - สร้าง Crypto Transaction
- `GET /api/crypto/transactions/{tx_hash}/status` - ตรวจสอบสถานะ Transaction
- `POST /api/crypto/transactions/{crypto_transaction_id}/update-status` - อัพเดทสถานะ
- `GET /api/crypto/stores/{store_id}/transactions` - ดึงรายการ Transactions

### Reports APIs
- `GET /api/reports/sales-tax` - รายงานภาษีขาย
- `GET /api/reports/separation-of-funds` - รายงานแยกประเภทเงิน
- `GET /api/reports/refund-summary` - รายงานสรุปการคืนเงิน
- `GET /api/reports/wht-calculation` - คำนวณ WHT
- `GET /api/reports/vat-calculation` - คำนวณ VAT

### Tax APIs
- `POST /api/tax/invoices/{transaction_id}` - สร้างใบกำกับภาษี
- `GET /api/tax/invoices/{invoice_id}` - ดึงข้อมูลใบกำกับภาษี
- `POST /api/tax/invoices/{invoice_id}/send-e-tax` - ส่ง E-Tax Invoice
- `GET /api/tax/invoices` - ดึงรายการใบกำกับภาษี

### Refund APIs (Admin)
- `GET /api/refunds/pending` - ดึงคำขอคืนเงินที่รอการประมวลผล
- `POST /api/refunds/{refund_request_id}/process` - ประมวลผลการคืนเงิน
- `POST /api/refunds/daily-reset` - เรียกใช้ Daily Balance Reset
- `POST /api/refunds/notify/{customer_id}` - ส่งการแจ้งเตือนคืนเงิน

## 7. Configuration

### config.ini Sections

#### [DATABASE]
- Database connection settings

#### [BACKEND]
- Backend URL, Secret Key, Debug mode

#### [E_MONEY]
- `HAS_E_MONEY_LICENSE`: มีใบอนุญาต e-Money หรือไม่
- `AUTO_REFUND_ENABLED`: เปิด/ปิดการแจ้งเตือนอัตโนมัติ
- `REFUND_NOTIFICATION_TIME`: เวลาที่จะส่งการแจ้งเตือน
- `DAILY_BALANCE_RESET`: รีเซ็ตยอดเงินทุกสิ้นวัน

#### [CRYPTO]
- Blockchain Explorer API URL
- Transaction Fee
- Monthly Flat Fee
- Enabled status

#### [TAX]
- WHT Rate (3%)
- VAT Rate (7%)
- Tax ID
- Company Name

#### [PAYMENT]
- PromptPay settings

#### [NOTIFICATION]
- LINE OA settings
- Push Notification settings

