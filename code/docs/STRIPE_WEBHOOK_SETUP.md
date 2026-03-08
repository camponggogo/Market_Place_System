# ตั้งค่า Stripe Webhook (ครั้งแรก)

ระบบมี endpoint รับ Webhook จาก Stripe อยู่แล้วที่:

```
POST /api/payment-callback/webhook/stripe
```

## ขั้นตอนลงทะเบียน Webhook ใน Stripe

### 1. เปิด Stripe Dashboard

ไปที่ **[Developers → Webhooks](https://dashboard.stripe.com/webhooks)** แล้วกด **Add endpoint**

### 2. ใส่ Endpoint URL

ใช้ URL นี้ (แทนที่ด้วยโดเมนจริงของคุณ หรือ ngrok):

**ตัวอย่างเมื่อใช้ ngrok:**
```
https://98b7-2405-9800-b651-70a4-85d3-2d7f-d6d2-d9eb.ngrok-free.app/api/payment-callback/webhook/stripe
```

**Production:** ใช้โดเมนจริง เช่น  
`https://yourdomain.com/api/payment-callback/webhook/stripe`

### 3. เลือก Event

เลือกอย่างน้อย:
- **payment_intent.succeeded**

(ถ้ามี event อื่นที่ต้องการ เช่น `payment_intent.payment_failed` ก็เลือกเพิ่มได้)

### 4. กด Add endpoint

### 5. Copy Signing secret

หลังสร้าง endpoint แล้ว:
1. เปิด endpoint นั้น
2. ใน **Signing secret** กด **Reveal**
3. Copy ค่าที่ขึ้นต้นด้วย `whsec_...`

### 6. ใส่ในระบบ

ใส่ใน `.env` (ที่ root โปรเจกต์):

```env
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxxxxxxxxxx
```

หรือใน `code/config.ini` ส่วน `[STRIPE]`:

```ini
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxxxxxxxxxx
```

จากนั้น **restart เซิร์ฟเวอร์** จึงจะใช้ค่าใหม่

---

## หมายเหตุ

- **ngrok:** ถ้า restart ngrok URL จะเปลี่ยน → ต้องไปแก้ endpoint ใน Stripe ให้ชี้ URL ใหม่ และถ้า Stripe ออก Signing secret ใหม่ ให้ copy ไปอัปเดตใน `.env` / config อีกครั้ง
- ดูรายละเอียดเพิ่ม: [STRIPE_NGROK.md](STRIPE_NGROK.md)
