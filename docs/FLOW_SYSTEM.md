# Flow ระบบ (System Flow) – Food Court Management System

เอกสารนี้อธิบาย **ลำดับการทำงาน** ของระบบว่าทำอะไรก่อน–หลัง และเชื่อมกันอย่างไร

---

## 1. สรุปภาพรวม

```
                    ┌─────────────────────────────────────────────────────────┐
                    │                  Backend (FastAPI :8000)                 │
                    │  config.ini, MySQL/MariaDB (market_place_system)        │
                    └─────────────────────────────────────────────────────────┘
                                         │
     ┌───────────────────────────────────┼───────────────────────────────────┐
     │                                   │                                   │
     ▼                                   ▼                                   ▼
┌─────────┐                      ┌─────────────┐                      ┌─────────────┐
│  Admin  │                      │ Store-POS   │                      │  Signage   │
│ /admin  │                      │ /store-pos  │                      │  /signage   │
│         │                      │             │                      │             │
│ ร้าน,   │                      │ สร้าง QR,   │◄──── state ──────────│ แสดง QR,   │
│ Banking,│                      │ ดู recent   │     (set-display,    │ ได้รับเงิน  │
│ Reports │                      │ paid        │      display, paid)  │ แล้ว, ack   │
└─────────┘                      └──────┬──────┘                      └──────┬──────┘
                                        │                                    │
                                        │ ref1 = store token (20 หลัก)       │
                                        ▼                                    │
                    ┌───────────────────────────────────────┐                │
                    │  ธนาคาร (SCB / K Bank)                  │                │
                    │  Webhook POST → /webhook หรือ           │                │
                    │  /webhook/kbank                         │                │
                    │  → บันทึก back_transaction              │                │
                    │  → set_signage_paid(store_id) ─────────┼────────────────┘
                    └───────────────────────────────────────┘
     │
     ▼
┌─────────┐    ┌─────────────┐
│ Counter │    │  Customer   │
│ exchange│    │  /customer  │
│ topup   │    │  balance,   │
│ refund  │    │  refund     │
└─────────┘    └─────────────┘
```

- **Backend เดียว** รันที่ port 8000 อ่าน config จาก `code/config.ini` และเชื่อม DB
- **หน้าเว็บ** (Admin, Store-POS, Signage, Customer) เปิดใน Browser เรียก API มาที่ Backend
- **ธนาคาร** ส่ง Webhook มาที่ Backend เมื่อลูกค้าจ่ายเงิน (ref1 = store token)

---

## 2. จุดเข้าใช้งาน (Entry Points)

| URL | หน้าที่ | ผู้ใช้ |
|-----|--------|--------|
| `/` | เปลี่ยนทางไป `/admin` | - |
| `/admin` | หน้า Admin (ร้าน, Banking, รายงาน, Store/Group/Site) | ผู้ดูแลระบบ |
| `/store-pos` | หน้า POS ร้าน (เลือกร้าน, สร้าง QR, ดูรายการจ่าย) | ร้านค้า |
| `/signage` | จอที่ 2 (แสดง QR / ได้รับเงินแล้ว) | จอลูกค้า |
| `/launch` | เปิด Store-POS + Signage พร้อมกัน (2 จอ) | เครื่อง POS |
| `/customer` | หน้าลูกค้า (ยอดคงเหลือ, ขอคืนเงิน) | ลูกค้า |
| `/customer-qr` | หน้า QR ลูกค้า | ลูกค้า |
| `/health` | ตรวจสอบว่า Backend ยังรันอยู่ | Monitoring |

---

## 3. ลำดับการทำงานหลัก (Flow ตามลำดับ)

### 3.1 เริ่มต้นระบบ (Startup)

1. รัน Backend: `uvicorn main:app` จากโฟลเดอร์ `code/` (หรือตาม Run script)
2. โหลด config จาก `code/config.ini` (หรือ env)
3. เชื่อม DB ตาม `[DATABASE]` → สร้างตารางถ้ายังไม่มี (`Base.metadata.create_all`)
4. Middleware: Security (rate limit), CORS
5. Mount static: `/static`, `/contracts`, `/static/imgs`
6. ลงทะเบียน routers: customer, stores, payment_callback, signage, admin, counter ฯลฯ

หลังรันแล้ว เปิด Browser ไปที่ `http://localhost:8000/admin` ได้เลย

---

### 3.2 Flow แอดมิน (Admin)

1. เปิด `/admin` → โหลด `admin_dashboard.html`
2. หน้าเว็บเรียก API เช่น:
   - `GET /api/stores/` → รายการร้าน (รวม group_id, site_id)
   - `GET /api/admin/statistics` → สถิติ
   - `GET /api/admin/banking-profiles` → โปรไฟล์ Banking
   - `GET /api/payment-callback/webhook/links` → ลิงก์ Webhook แยก SCB / K Bank
3. จัด Site / Group / Store: ลากร้านไปวางที่ Group หรือ double-click แก้ไข → `PATCH /api/stores/{id}` (site_id, group_id)
4. เพิ่มร้าน: `POST /api/stores/` (ชื่อ, tax_id, group_id, site_id)
5. ตั้งค่า Banking Profile: ใส่ SCB (API Key, Secret, Callback URL) และ/หรือ K Bank (Customer ID, Consumer Secret) แล้วบันทึก
6. รายงาน: เรียก API reports / payment / transactions ตามแท็บที่เลือก

ลำดับที่ควรทำครั้งแรก: สร้างร้าน → ตั้ง Banking (และลงทะเบียน Webhook URL กับธนาคาร) → ใช้แท็บ Stores จัด Site/Group ถ้าต้องการ

---

### 3.3 Flow เคาน์เตอร์ (Counter) – แลก / เติม / คืน Food Court ID

1. **แลกเงินเป็น Food Court ID**
   - เรียก `POST /api/counter/exchange` (amount, payment_method)
   - Backend สร้าง `FoodCourtID` ใน DB → คืน `foodcourt_id` (รหัสให้ลูกค้า)
2. **เติมเงิน (Top-up)**
   - เรียก `POST /api/counter/topup` (foodcourt_id, amount, payment_method)
3. **คืนเงิน (Refund)**
   - เรียก `POST /api/counter/refund` (foodcourt_id)
4. **ตรวจยอด**
   - เรียก `GET /api/counter/balance/{foodcourt_id}`

ลำดับ: ลูกค้ามาเคาน์เตอร์ → แลก (exchange) → ได้รหัส Food Court ID → ไปใช้ที่ร้าน (payment-hub use)

---

### 3.4 Flow ร้าน (Store-POS) + จอ Signage + ธนาคาร (PromptPay)

นี่คือ flow หลักเวลาลูกค้าจ่ายด้วย PromptPay ที่ร้าน

**ขั้นที่ 1: ร้านกดสร้าง QR**

1. เปิด `/store-pos?store_id=1` (หรือเลือกร้านในหน้า)
2. เลือกเมนู/จำนวนเงิน (หรือ Quick Amount) แล้วกดสร้าง QR
3. หน้า Store-POS เรียก:
   - `GET /api/stores/{store_id}` (หรือใช้ cache) → ได้ store.token (ref1)
   - `POST /api/stores/{store_id}/generate-promptpay-qr` (amount, menu_id ฯลฯ) → ได้รูป QR (base64)
   - `POST /api/signage/set-display` (store_id, qr_image, amount) → ส่งไปจอ Signage

**ขั้นที่ 2: จอ Signage แสดง QR**

1. เปิด `/signage?store_id=1` (จอที่ 2)
2. จอ Signage **poll** `GET /api/signage/display?store_id=1` เป็นระยะ
3. เมื่อ Backend ได้รับ set-display แล้ว → การ poll จะได้ `status: "waiting_payment"`, `qr_image`, `amount`
4. จอ Signage แสดง QR และจำนวนเงินให้ลูกค้าสแกน

**ขั้นที่ 3: ลูกค้าสแกน QR และจ่ายในแอปธนาคาร**

- ลูกค้าเปิดแอป SCB / K Bank ฯลฯ สแกน QR แล้วยืนยันจ่าย
- ธนาคารประมวลผลและจะส่ง Webhook มาที่ Backend (ไม่เกี่ยวกับจอ Signage โดยตรง)

**ขั้นที่ 4: ธนาคารส่ง Webhook มา Backend**

1. ธนาคารเรียก:
   - **SCB:** `POST /api/payment-callback/webhook`
   - **K Bank:** `POST /api/payment-callback/webhook/kbank`
2. Body มีอย่างน้อย: **ref1** (= store token 20 หลัก), **amount**, (ref2, ref3 ฯลฯ)
3. Backend ทำตามลำดับ:
   - แปลง ref1 → หา `store_id` จากตาราง `stores` (field `token`)
   - บันทึก `promptpay_back_transactions` และสร้าง/อัปเดต `transactions`
   - เรียก **`set_signage_paid(store_id)`** → state จอ Signage เปลี่ยนเป็น "paid"
   - ตอบ **200 OK** ทันที (เพื่อไม่ให้ธนาคาร retry)

**ขั้นที่ 5: จอ Signage แสดง "ได้รับเงินแล้ว"**

1. จอ Signage ยังคง poll `GET /api/signage/display?store_id=1`
2. ได้ `status: "paid"` → แสดงข้อความ "ได้รับเงินเรียบร้อยแล้ว" + จำนวนเงิน (และออกเสียงถ้ามี)
3. หลังแสดงเสร็จ เรียก `POST /api/signage/ack-paid?store_id=1` → Backend เคลียร์ state (กลับโหมด idle/signage)

**ขั้นที่ 6: Store-POS รู้ว่ามีเงินเข้า**

1. หน้า Store-POS อาจ **poll** `GET /api/payment-callback/stores/{store_id}/recent-paid?since=...` เพื่อแสดงรายการ "จ่ายแล้ว" ล่าสุด
2. ข้อมูลรายการมาจากตาราง `promptpay_back_transactions` / `transactions` ที่บันทึกจาก Webhook

ลำดับสั้นๆ: **Store-POS สร้าง QR → set-display → Signage แสดง QR → ลูกค้าจ่าย → Bank Webhook → บันทึก DB + set_signage_paid → Signage แสดง paid → ack-paid**

---

### 3.5 Flow ลูกค้า (Customer)

1. เปิด `/customer` (หรือ `/customer-qr`)
2. ลงทะเบียน/ล็อกอิน (ถ้ามี) → เรียก API ลูกค้า
3. ตรวจยอด: `GET /api/customers/{id}/balance` หรือผ่าน payment-hub/balance
4. ขอคืนเงิน: เรียก API refund ตามที่ระบบออกแบบ (pending → process)

---

### 3.6 Flow สรุปยอดและโอน (Settlement)

1. **สร้างสรุปรายวัน**
   - เรียก `POST /api/payment-callback/settlements/create-daily` (หรือตาม cron)
   - Backend รวมยอดจาก `promptpay_back_transactions` ต่อร้านต่อวัน → สร้าง/อัปเดต `store_settlements`
2. **ดูรายการ**
   - `GET /api/payment-callback/settlements`
3. **บันทึกว่าโอนแล้ว**
   - `POST /api/payment-callback/settlements/{id}/mark-transferred`
4. **แจ้งร้าน**
   - `POST /api/payment-callback/settlements/{id}/notify-store`

---

## 4. การไหลของข้อมูลสำคัญ

| ข้อมูล | ที่มา | การใช้ |
|--------|------|--------|
| **store.token** (20 หลัก) | ตาราง `stores` (สร้างจาก group_id+site_id+store_id+menu_id) | ใส่ใน QR เป็น **ref1** |
| **ref1** | ธนาคารส่งใน Webhook | ใช้หา `store_id` (WHERE token = ref1) แล้วบันทึก transaction + เรียก set_signage_paid(store_id) |
| **store_id** | จาก ref1 ผ่านตาราง stores | ใช้กับ signage state (display, paid, ack-paid) และ recent-paid, settlements |
| **Signage state** | In-memory ต่อ store_id (qr_image, amount, status) | จอ Signage poll display; หลัง paid → แสดง "ได้รับเงินแล้ว" แล้ว ack-paid |

---

## 5. API ที่เกี่ยวกับ Flow หลัก (สรุป)

| กลุ่ม | Method | Path (ตัวอย่าง) | ใช้เมื่อ |
|--------|--------|------------------|----------|
| Stores | GET | `/api/stores/`, `/api/stores/{id}` | โหลดร้าน, สร้าง QR |
| Stores | POST | `/api/stores/{id}/generate-promptpay-qr` | สร้าง QR |
| Signage | POST | `/api/signage/set-display` | Store-POS ส่ง QR ไปจอ |
| Signage | GET | `/api/signage/display?store_id=` | จอ Signage poll |
| Signage | POST | `/api/signage/ack-paid?store_id=` | จอแสดง "ได้รับเงินแล้ว" เสร็จ |
| Payment Callback | POST | `/api/payment-callback/webhook` | SCB ส่งผลชำระ |
| Payment Callback | POST | `/api/payment-callback/webhook/kbank` | K Bank ส่งผลชำระ |
| Payment Callback | GET | `/api/payment-callback/stores/{id}/recent-paid` | Store-POS ดูรายการจ่ายล่าสุด |
| Counter | POST | `/api/counter/exchange` | แลก Food Court ID |
| Admin | GET/POST/PUT | `/api/admin/*` | จัดการร้าน, Banking, รายงาน |

---

## 6. ไฟล์/โฟลเดอร์ที่เกี่ยวกับ Flow

| ส่วน | โฟลเดอร์/ไฟล์ |
|------|----------------|
| จุดเข้าแอป | `code/main.py` (routes /, /admin, /store-pos, /signage, mount static) |
| Config | `code/config.ini`, `code/app/config.py` |
| DB | `code/app/database.py`, `code/app/models.py` |
| Webhook + บันทึก transaction | `code/app/api/payment_callback.py`, `code/app/services/settlement_service.py` |
| Signage state | `code/app/api/signage.py` (in-memory ต่อ store_id) |
| สร้าง QR | `code/app/api/stores.py` (generate-promptpay-qr), `code/app/services/promptpay*.py` |
| หน้าเว็บ | `code/app/static/*.html` (admin_dashboard, store_pos, signage, customer ฯลฯ) |

เอกสารนี้ใช้ดู **ลำดับการทำงานของระบบ** โดยรวม สำหรับรายละเอียด Bank/Webhook และการรัน ให้ดู `docs/ARCHITECTURE_BANK_AND_RUN.md` ด้วย
