# Webhook Gateway (VMS)

รันบน Docker cloud รับ Webhook แล้ว **บันทึกลง Database** เสมอ และ **เลือกบันทึกลงไฟล์** `data/{YYYY-MM-DD}/{source}/*.json` ตาม config

## Endpoints

| Method | Path | คำอธิบาย |
|--------|------|----------|
| GET/POST | / | สถานะและรายการ endpoints |
| POST | /status | Status change callback → บันทึก DB + (ถ้าเปิด) ไฟล์ data/{date}/status_change/*.json |
| POST | /paysuccess | Payment success → บันทึก DB + (ถ้าเปิด) ไฟล์ data/{date}/paysuccess/*.json |
| POST | /well2pay | Well2Pay callback → บันทึก DB + (ถ้าเปิด) ไฟล์ data/{date}/well2pay/*.json |

## Auth กับ API ธนาคาร (ลายเซ็น Webhook)

ถ้าธนาคารส่ง **ลายเซ็น** มา (เช่น HMAC-SHA256 ของ body) ตั้งค่าใน config:

- **[WEBHOOK] WEBHOOK_SECRET** = รหัสลับที่ลงทะเบียนกับธนาคาร (ใช้คำนวณลายเซ็น)
- Header ที่รองรับ: **X-Signature**, **X-Webhook-Signature**, **X-Hub-Signature-256** (รูปแบบ `sha256=<hex>` หรือแค่ `<hex>`)
- ถ้าไม่ตั้ง WEBHOOK_SECRET = ไม่ตรวจลายเซ็น (รับทุก request)

## Config (config.ini หรือ Environment)

- **[DATABASE]** – ใช้ DB ตัวเดียวกับ Food Court ได้  
  `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
- **[WEBHOOK]**  
  - **SAVE_TO_FILES** = `true` / `false` – เปิด/ปิดการบันทึกลงไฟล์  
  - **DATA_DIR** = `data` – โฟลเดอร์ฐาน (path จริงจะเป็น `data/{YYYY-MM-DD}/{source}/*.json`)
  - **WEBHOOK_SECRET** – รหัสลับสำหรับตรวจลายเซ็นจากธนาคาร (ว่าง = ไม่ตรวจ)

## ตาราง DB

ตาราง `webhook_logs` (สร้างอัตโนมัติเมื่อรันครั้งแรกถ้ายังไม่มี):

- `id` (PK)
- `source` (paysuccess, status_change, well2pay)
- `payload` (JSON)
- `received_at` (datetime)

SQL ต้นแบบ: `init_webhook_log.sql`

## รัน local

```bash
cd webhook_gateway
pip install -r requirements.txt
python webhook.py
```

รันที่ port 80 (หรือตั้ง `PORT=5000` ใน env)

## Docker

ใช้ Dockerfile หรือ bind mount โฟลเดอร์นี้แล้วรัน `python webhook.py` ใน container; ตั้ง env หรือ mount `config.ini` ให้ตรงกับ DB และตัวเลือก SAVE_TO_FILES / DATA_DIR
