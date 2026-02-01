# API Documentation – Market_Place_System

เอกสาร API สำหรับ Developer ใช้เรียก REST API ของระบบ Market_Place_System

---

## ข้อมูลทั่วไป

- **Base URL:** `http://localhost:8000` (หรือ URL ของ Server ที่ deploy แล้ว)
- **Content-Type:** `application/json`
- **Authentication:** ปัจจุบัน API ส่วนใหญ่ไม่ใช้ Bearer Token (ปรับได้ตามนโยบายความปลอดภัย)

---

## สารบัญ

1. [Health](#1-health)
2. [Stores (ร้านค้า)](#2-stores-ร้านค้า)
3. [Store Quick Amounts](#3-store-quick-amounts)
4. [Menus (เมนู)](#4-menus-เมนู)
5. [Counter (จุดแลกเงิน)](#5-counter-จุดแลกเงิน)
6. [Payment Hub (หักยอด/ยอดคงเหลือ)](#6-payment-hub-หักยอดยอดคงเหลือ)
7. [Payment Callback & Webhook](#7-payment-callback--webhook)
8. [Signage (จอที่ 2)](#8-signage-จอที่-2)
9. [Admin](#9-admin)
10. [Customer](#10-customer)
11. [Reports](#11-reports)
12. [Tax / Invoices](#12-tax--invoices)
13. [Refund](#13-refund)
14. [Profiles & Events](#14-profiles--events)
15. [Geo (ตำแหน่งร้าน)](#15-geo-ตำแหน่งร้าน)
16. [Crypto (E-Contract)](#16-crypto-e-contract)

---

## 1. Health

| Method | Path | คำอธิบาย |
|--------|------|----------|
| GET | `/health` | ตรวจสอบสถานะ API |

**Response 200:**
```json
{ "status": "healthy" }
```

---

## 2. Stores (ร้านค้า)

Base path: `/api/stores`

| Method | Path | คำอธิบาย |
|--------|------|----------|
| POST | `/api/stores/` | สร้างร้านค้าใหม่ (และสร้าง Store Token 20 หลัก) |
| GET | `/api/stores/` | รายการร้านค้าทั้งหมด |
| GET | `/api/stores/{store_id}` | ดึงข้อมูลร้านค้าตาม ID |
| POST | `/api/stores/{store_id}/generate-promptpay-qr` | สร้าง PromptPay QR (Tag30 + Tag29 ถ้ามีเบอร์) |
| POST | `/api/stores/{store_id}/generate-bot-standard-qr` | สร้าง Bot Standard QR (EMVCo) |

### POST `/api/stores/` – สร้างร้านค้า

**Request body:**
```json
{
  "name": "ชื่อร้าน",
  "tax_id": "1234567890123",
  "group_id": 0,
  "site_id": 0,
  "biller_id": "011556400219809"
}
```

**Response 200:** ข้อมูลร้านรวม `id`, `token`, `biller_id`

### POST `/api/stores/{store_id}/generate-promptpay-qr` – สร้าง QR

**Request body:**
```json
{
  "menu_id": 1,
  "ref3": "หมายเหตุ",
  "amount": 150.50,
  "promptpay_mobile": "0812345678"
}
```

**Response 200:**
```json
{
  "qr_code_tag30": "data:image/png;base64,...",
  "qr_code_tag30_static": "data:image/png;base64,...",
  "qr_code_tag29": "data:image/png;base64,..."
}
```

---

## 3. Store Quick Amounts

Base path: `/api/stores/{store_id}/quick-amounts`

| Method | Path | คำอธิบาย |
|--------|------|----------|
| GET | `/api/stores/{store_id}/quick-amounts/` | รายการปุ่มราคาด่วน |
| POST | `/api/stores/{store_id}/quick-amounts/` | เพิ่มราคาด่วน |
| PUT | `/api/stores/{store_id}/quick-amounts/{quick_amount_id}` | แก้ไขราคาด่วน |
| DELETE | `/api/stores/{store_id}/quick-amounts/{quick_amount_id}` | ลบราคาด่วน |

**POST body:** `{ "amount": 100, "label": "100 บาท" }`

---

## 4. Menus (เมนู)

Base path: `/api/menus`

| Method | Path | คำอธิบาย |
|--------|------|----------|
| POST | `/api/menus/` | สร้างเมนู |
| GET | `/api/menus/store/{store_id}` | รายการเมนูของร้าน |
| GET | `/api/menus/{menu_id}` | ดึงเมนูตาม ID |
| PUT | `/api/menus/{menu_id}` | แก้ไขเมนู |
| DELETE | `/api/menus/{menu_id}` | ลบเมนู |

**Create body:** `{ "store_id": 1, "name": "ข้าวผัด", "description": "...", "unit_price": 45.00, "is_active": true }`

---

## 5. Counter (จุดแลกเงิน)

Base path: `/api/counter`

| Method | Path | คำอธิบาย |
|--------|------|----------|
| POST | `/api/counter/exchange` | แลกเงินเป็น Food Court ID |
| GET | `/api/counter/balance/{foodcourt_id}` | ตรวจสอบยอดคงเหลือ (Food Court ID) |
| POST | `/api/counter/refund` | คืนเงินตาม Food Court ID |
| POST | `/api/counter/topup` | Top-up ยอดเพิ่มให้ Food Court ID |
| GET | `/api/counter/payment-methods` | รายการวิธีชำระเงินที่รองรับ |
| GET | `/api/counter/foodcourt-ids` | รายการ Food Court ID (สำหรับค้นหา) |

### POST `/api/counter/exchange`

**Request body:**
```json
{
  "amount": 500,
  "payment_method": "cash",
  "payment_details": null,
  "counter_id": 1,
  "counter_user_id": 1,
  "customer_id": null
}
```

**Response 200:** `{ "success": true, "foodcourt_id": "FC-...", "amount": 500, "payment_method": "cash", "created_at": "..." }`

### POST `/api/counter/refund`

**Request body:** `{ "foodcourt_id": "FC-...", "counter_id": 1, "counter_user_id": 1 }`

### POST `/api/counter/topup`

**Request body:** `{ "foodcourt_id": "FC-...", "amount": 100, "payment_method": "cash", ... }`

---

## 6. Payment Hub (หักยอด/ยอดคงเหลือ)

Base path: `/api/payment-hub`

| Method | Path | คำอธิบาย |
|--------|------|----------|
| POST | `/api/payment-hub/use` | หักยอดเงินที่ร้าน (ใช้ Food Court ID) |
| GET | `/api/payment-hub/balance/{foodcourt_id}` | ดูยอดคงเหลือของ Food Court ID |

### POST `/api/payment-hub/use`

**Request body:**
```json
{
  "foodcourt_id": "FC-20241201-00001",
  "store_id": 1,
  "amount": 150
}
```

**Response 200:** `{ "success": true, "remaining_balance": 350, ... }`

---

## 7. Payment Callback & Webhook

Base path: `/api/payment-callback`

| Method | Path | คำอธิบาย |
|--------|------|----------|
| GET | `/api/payment-callback/webhook` | Health check สำหรับ Webhook URL |
| POST | `/api/payment-callback/webhook` | รับ Back Transaction จากธนาคาร (Webhook) |
| POST | `/api/payment-callback/back-transaction` | รับ Back Transaction (ใช้ payload เดียวกับ webhook) |
| GET | `/api/payment-callback/back-transactions/report` | รายงาน Back Transactions |
| GET | `/api/payment-callback/settlements` | รายการ Settlement (โอนสิ้นวัน) |
| POST | `/api/payment-callback/settlements/create-daily` | สร้างรายการ Settlement รายวัน |
| POST | `/api/payment-callback/settlements/{id}/mark-transferred` | บันทึกว่าโอนเงินแล้ว |
| POST | `/api/payment-callback/settlements/{id}/notify-store` | แจ้งร้าน (สำหรับพิมพ์ใบเสร็จ) |
| GET | `/api/payment-callback/stores/{store_id}/recent-paid` | รายการจ่ายล่าสุดของร้าน (สำหรับ POS poll) |
| GET | `/api/payment-callback/stores/{store_id}/settlements-for-receipt` | รายการ Settlement สำหรับพิมพ์ใบเสร็จ |

### POST `/api/payment-callback/webhook` (Back Transaction)

**Request body:**
```json
{
  "ref1": "00000010000010000000",
  "amount": 150.50,
  "paid_at": "2024-01-15T10:30:00",
  "ref2": null,
  "ref3": "หมายเหตุ",
  "slip_reference": "SLIP123",
  "bank_account": "123-4-56789-0",
  "raw_payload": {}
}
```

- **ref1:** Store Token 20 หลัก  
- **amount:** ยอดเงิน  
- **paid_at:** เวลาชำระ (ISO format, optional)

---

## 8. Signage (จอที่ 2)

Base path: `/api/signage`

| Method | Path | คำอธิบาย |
|--------|------|----------|
| POST | `/api/signage/set-display` | ตั้งค่าสิ่งที่จอ Signage แสดง (QR + ยอด) |
| GET | `/api/signage/display?store_id=1` | ดึงสถานะปัจจุบันของจอ (สำหรับ Signage poll) |
| POST | `/api/signage/ack-paid?store_id=1` | แจ้งว่าแสดง "ได้รับเงินเรียบร้อยแล้ว" แล้ว (กลับโหมด default) |
| POST | `/api/signage/clear?store_id=1` | ล้างจอ Signage (ยกเลิกการจ่าย / ทำรายการใหม่) |

### POST `/api/signage/set-display`

**Request body:** `{ "store_id": 1, "qr_image": "data:image/png;base64,...", "amount": 150.50 }`

### GET `/api/signage/display?store_id=1`

**Response 200:** `{ "status": "waiting_payment" | "paid" | null, "qr_image": "...", "amount": 150.50 }`

---

## 9. Admin

Base path: `/api/admin`

| Method | Path | คำอธิบาย |
|--------|------|----------|
| GET | `/api/admin/statistics` | สถิติภาพรวมระบบ |
| GET | `/api/admin/transactions` | รายการธุรกรรม |
| GET | `/api/admin/customers` | รายการลูกค้า |
| POST | `/api/admin/customers/link-foodcourt-id` | ผูก Food Court ID กับลูกค้า |
| DELETE | `/api/admin/customers/{customer_id}/foodcourt-id/{foodcourt_id}` | ยกเลิกการผูก Food Court ID |

---

## 10. Customer

Base path: `/api/customers`

| Method | Path | คำอธิบาย |
|--------|------|----------|
| POST | `/api/customers/register` | ลงทะเบียนลูกค้า |
| POST | `/api/customers/check-balance` | ตรวจสอบยอดคงเหลือ (ด้วย Food Court ID หรือข้อมูลอื่น) |
| GET | `/api/customers/{customer_id}/balance` | ยอดคงเหลือของลูกค้า |
| POST | `/api/customers/refund` | ขอคืนเงิน |
| GET | `/api/customers/{customer_id}/refund-requests` | รายการขอคืนเงิน |
| POST | `/api/customers/generate-qr/{customer_id}` | สร้าง QR สำหรับลูกค้า |

---

## 11. Reports

Base path: `/api/reports` และ `/api/reports-payment`

### `/api/reports`

| Method | Path | คำอธิบาย |
|--------|------|----------|
| GET | `/api/reports/sales-tax` | รายงานภาษีขาย |
| GET | `/api/reports/separation-of-funds` | รายงาน Separation of Funds |
| GET | `/api/reports/refund-summary` | สรุปการคืนเงิน |
| GET | `/api/reports/wht-calculation` | คำนวณ WHT |
| GET | `/api/reports/vat-calculation` | คำนวณ VAT |

### `/api/reports-payment`

| Method | Path | คำอธิบาย |
|--------|------|----------|
| GET | `/api/reports-payment/store/{store_id}` | รายงานการชำระเงินของร้าน |
| GET | `/api/reports-payment/daily` | รายงานรายวัน |
| GET | `/api/reports-payment/monthly` | รายงานรายเดือน |
| GET | `/api/reports-payment/yearly` | รายงานรายปี |

---

## 12. Tax / Invoices

Base path: `/api/tax`

| Method | Path | คำอธิบาย |
|--------|------|----------|
| POST | `/api/tax/invoices/{transaction_id}` | สร้างใบกำกับภาษี |
| GET | `/api/tax/invoices/{invoice_id}` | ดึงใบกำกับภาษี |
| POST | `/api/tax/invoices/{invoice_id}/send-e-tax` | ส่ง E-Tax Invoice |
| GET | `/api/tax/invoices` | รายการใบกำกับภาษี |

---

## 13. Refund

Base path: `/api/refund`

| Method | Path | คำอธิบาย |
|--------|------|----------|
| GET | `/api/refund/pending` | รายการรอคืนเงิน |
| POST | `/api/refund/{refund_request_id}/process` | ดำเนินการคืนเงิน |
| POST | `/api/refund/daily-reset` | รีเซ็ตรายวัน |
| POST | `/api/refund/notify/{customer_id}` | แจ้งเตือนลูกค้า |

---

## 14. Profiles & Events

Base path: `/api/profiles` และ `/api/profiles/events`

| Method | Path | คำอธิบาย |
|--------|------|----------|
| POST | `/api/profiles/` | สร้าง Profile |
| GET | `/api/profiles/` | รายการ Profile |
| GET | `/api/profiles/{profile_id}` | ดึง Profile |
| POST | `/api/profiles/events/` | สร้าง Event |
| GET | `/api/profiles/events/` | รายการ Event |
| GET | `/api/profiles/events/{event_id}` | ดึง Event |

---

## 15. Geo (ตำแหน่งร้าน)

Base path: `/api/geo`

| Method | Path | คำอธิบาย |
|--------|------|----------|
| GET | `/api/geo/stores` | รายการร้านพร้อมตำแหน่ง |
| PUT | `/api/geo/stores/{store_id}/location` | อัปเดตตำแหน่งร้าน |

---

## 16. Crypto (E-Contract)

Base path: `/api/crypto`

| Method | Path | คำอธิบาย |
|--------|------|----------|
| GET | `/api/crypto/stores/{store_id}/contract-status` | สถานะสัญญาร้าน |
| POST | `/api/crypto/stores/accept-contract` | ร้านยอมรับสัญญา |
| POST | `/api/crypto/transactions` | สร้างธุรกรรม Crypto |
| GET | `/api/crypto/transactions/{tx_hash}/status` | สถานะธุรกรรม |
| POST | `/api/crypto/transactions/{id}/update-status` | อัปเดตสถานะ |
| GET | `/api/crypto/stores/{store_id}/transactions` | รายการธุรกรรมร้าน |
| GET | `/api/crypto/fee/transaction` | ค่าธรรมเนียมธุรกรรม |

---

## หมายเหตุ

- เปิด **Swagger UI** ที่ `/docs` เมื่อตั้ง `ENABLE_DOCS=true`  
- เปิด **ReDoc** ที่ `/redoc` เมื่อตั้ง `ENABLE_DOCS=true`  
- รหัสข้อผิดพลาด: ใช้ HTTP status ตามมาตรฐาน (400 Bad Request, 404 Not Found, 500 Internal Server Error) และ `detail` ใน JSON response  
