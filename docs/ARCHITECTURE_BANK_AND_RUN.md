# โครงสร้างระบบ: Bank API + Webhook และการแยกรัน Front-end / Back-end

## สรุป

- **Back-end (ตัวเดียว)** = FastAPI ที่เชื่อม Database, รับ Webhook จาก SCB และ K Bank (PromptPay), บันทึกลง DB และอัปเดต Signage ให้ทำงานสอดประสาน
- **Front-end** = หน้าเว็บ (Customer, Store-POS, Admin, Signage) ที่เปิดใน Browser เรียก API ไปที่ Back-end

---

## 1. Back-end (รันหนึ่ง process)

รันที่ **port 8000** (หรือตาม config):

- **Database** – เชื่อม MySQL/MariaDB ตาม `config.ini` / env
- **API ภายใน** – stores, menus, payment-callback, signage, admin, customer ฯลฯ
- **Bank / PromptPay**
  - **SCB** – ใช้ค่าจาก `scb.note` (หรือ Store.scb_*) ลงทะเบียน Webhook URL กับ SCB
  - **K Bank** – ใช้ค่าจาก `K_API.note` (หรือ Store.kbank_*) สำหรับ OAuth และลงทะเบียน Webhook กับ K API

### Webhook ที่ Back-end ต้องเปิดให้ธนาคารเรียก (HTTPS ใน production)

| ธนาคาร   | Method | URL ที่ลงทะเบียนกับธนาคาร | ใช้สำหรับ |
|----------|--------|----------------------------|-----------|
| **SCB**  | POST   | `https://<โดเมน>/api/payment-callback/webhook` | รับผลชำระ PromptPay จาก SCB |
| **K Bank** | POST | `https://<โดเมน>/api/payment-callback/webhook/kbank` | รับผลชำระ QR Payment จาก K Bank |

เมื่อธนาคารส่ง callback มา Back-end จะ (ทำตามลำดับและตอบกลับเร็ว):

1. รับ payload (ref1 = store token, amount, ref2, ref3 ฯลฯ)
2. บันทึกลง `promptpay_back_transactions` และสร้าง/อัปเดต `transactions` ทันที
3. เรียก `set_signage_paid(store_id)` เพื่อให้จอ Signage / Store-POS แสดง "ได้รับเงินแล้ว"
4. คืน **200 OK** ทันทีหลังบันทึก DB เพื่อให้ธนาคารไม่ retry และระบบทำงานรวดเร็ว

---

## 2. Front-end (เปิดใน Browser)

ทุกหน้ารันจาก **Back-end เดียวกัน** (serve static + API) ไม่มีแอป front-end แยก process:

| หน้าที่        | URL (เมื่อ Back-end = http://localhost:8000) | ผู้ใช้ |
|----------------|-----------------------------------------------|--------|
| **Admin**      | http://localhost:8000/admin                   | ผู้ดูแลระบบ |
| **Store-POS**  | http://localhost:8000/store-pos?store_id=1    | ร้านค้า (กดสร้าง QR, ดูรายการจ่าย) |
| **Signage**    | http://localhost:8000/signage?store_id=1      | จอลูกค้า (แสดง QR / ได้รับเงินแล้ว) |
| **Customer**   | http://localhost:8000/customer                | ลูกค้า (ดูยอด, ขอคืนเงิน ฯลฯ) |
| **Launch (POS+Signage)** | http://localhost:8000/launch?store_id=1 | เปิด Store-POS + Signage พร้อมกัน (2 จอ) |

Front-end ทุกหน้าเรียก **API ที่ Back-end** (เช่น `/api/stores/`, `/api/signage/display`, `/api/payment-callback/stores/{id}/recent-paid`) จึงต้องรัน Back-end ก่อนแล้วค่อยเปิด URL เหล่านี้

---

## 3. Flow การทำงานสอดประสาน (PromptPay)

```
[Store-POS] กดสร้าง QR
    → POST /api/signage/set-display (store_id, amount, qr_image)
    → Back-end บันทึก state, จอ Signage แสดง QR

[ลูกค้า] สแกน QR จ่ายผ่านแอปธนาคาร (SCB / K Bank ฯลฯ)

[ธนาคาร] ส่ง Webhook มาที่ Back-end
    → POST /api/payment-callback/webhook (SCB)
    → หรือ POST /api/payment-callback/webhook/kbank (K Bank)
    → Back-end: บันทึก promptpay_back_transactions + transactions
    → set_signage_paid(store_id)
    → คืน 200 OK

[Signage / Store-POS] poll หรือรับ state
    → GET /api/signage/display?store_id=1 → status=paid, amount
    → แสดง "ได้รับเงิน xxx บาท แล้ว" / ออกเสียง
    → เรียก POST /api/signage/ack-paid เมื่อแสดงเสร็จ
```

การตอบ Webhook เร็ว (บันทึก DB + อัปเดต state แล้วคืน 200 ทันที) ช่วยให้ธนาคารไม่ retry ซ้ำและระบบรู้สถานะ "จ่ายแล้ว" ได้ทันที

---

## 4. การรันแยก Back-end และ Front-end

### รัน Back-end (ต้องรันก่อนเสมอ)

```powershell
# จากโฟลเดอร์ Run
.\Run\start_backend.ps1
```

หรือมือ:

```powershell
$env:PYTHONPATH = "D:\Projects\FoodCourt\code"
cd D:\Projects\FoodCourt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

(รันจาก project root โดยให้ Python โหลด `code` ได้ เช่น `PYTHONPATH=code`)

### เปิด Front-end (หลัง Back-end รันแล้ว)

```powershell
.\Run\start_frontend.ps1
```

จะเปิด Browser ไปที่ Admin, Store-POS, Signage (และ Launch ถ้องการ) ชี้ไปที่ `http://localhost:8000`

### รัน Back-end แล้วเปิด Front-end ในคำสั่งเดียว

```powershell
.\Run\start_all.ps1
```

---

## 5. Config ที่เกี่ยวกับ Bank

- **SCB** – `scb.note` หรือ config/Store: `scb_api_key`, `scb_api_secret`, `scb_callback_url` (ลงทะเบียนกับ SCB = URL ของ Back-end ด้านบน)
- **K Bank** – `K_API.note` หรือ config/Store: `kbank_customer_id`, `kbank_consumer_secret`; OAuth token URL ใน config สำหรับเรียก K API อื่น (Inward Remittance ฯลฯ)
- **Database** – `config.ini` [DATABASE] หรือ env ให้ชี้ไปที่ DB ชุดเดียวที่ Back-end ใช้

เมื่อตั้งครบ Back-end จะรับ Webhook จากทั้ง SCB และ K Bank แล้วบันทึกลง DB และอัปเดต Signage/Store-POS ให้ทำงานสอดประสานและรวดเร็วตาม flow ด้านบน
