# Stripe Webhook + ngrok (ทดสอบบนเครื่องตัวเอง)

`STRIPE_WEBHOOK_SECRET` **ไม่ได้สร้างเอง** — Stripe จะให้ค่าหลังจากคุณเพิ่ม Webhook endpoint และใช้ URL จาก ngrok

## ขั้นตอน

### 1. รัน ngrok

```bash
ngrok http 8000
```

(หรือพอร์ตที่คุณรัน uvicorn เช่น 8000)

จากนั้นจะได้ URL แบบนี้: `https://xxxx-xx-xx-xx-xx.ngrok-free.app`

### 2. ลงทะเบียน Webhook ใน Stripe

1. เปิด [Stripe Dashboard → Developers → Webhooks](https://dashboard.stripe.com/webhooks)
2. กด **Add endpoint**
3. **Endpoint URL** ใส่:
   ```text
   https://xxxx-xx-xx-xx-xx.ngrok-free.app/api/payment-callback/webhook/stripe
   ```
   (แทน `xxxx-xx-xx-xx-xx` ด้วย subdomain จริงจาก ngrok)
4. เลือก Events อย่างน้อย: **payment_intent.succeeded**
5. กด **Add endpoint**

### 3. Copy Signing secret

หลังสร้าง endpoint แล้ว:

1. เปิด endpoint ที่สร้างไว้
2. ใน **Signing secret** กด **Reveal**
3. Copy ค่าที่ขึ้นต้นด้วย `whsec_...`

### 4. ใส่ใน config

**แบบ config.ini**

ใน `code/config.ini` ส่วน `[STRIPE]`:

```ini
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxxxxxxxxxx
```

**แบบ Environment variable**

```bash
set STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxxxxxxxxxx
```

จากนั้นรันเซิร์ฟเวอร์ใหม่ แล้วส่ง event ทดสอบจาก Stripe Dashboard (Send test webhook) ได้

## หมายเหตุ

- เวลาใช้ ngrok ใหม่ (restart) URL จะเปลี่ยน → ต้องไปเพิ่ม/แก้ endpoint ใน Stripe ให้ชี้ URL ใหม่ และถ้า Stripe ออก **Signing secret ใหม่** ให้ copy ไปใส่ใน config อีกครั้ง
- ถ้าใช้ **Stripe CLI** (`stripe listen --forward-to localhost:8000/api/payment-callback/webhook/stripe`) ค่า `whsec_...` ที่ CLI แสดงคือ secret สำหรับ local; ใส่ค่านั้นใน `STRIPE_WEBHOOK_SECRET` ได้เลย
