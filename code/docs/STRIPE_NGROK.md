# Stripe Webhook + ngrok (ทดสอบบนเครื่องตัวเอง)

**แนวทาง deploy บน Cloud Docker (รวมกรณีไม่มี SSL):** ดูใน `code/docs/STRIPE_CLI_VS_API.md`

ระบบใช้ **Stripe API** (ลงทะเบียน Webhook URL ใน Dashboard) เป็นหลัก — `STRIPE_WEBHOOK_SECRET` ได้จาก Stripe Dashboard หลังเพิ่ม endpoint และใช้ URL จาก ngrok หรือโดเมน

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

## ติดตั้ง Stripe CLI (Windows)

ถ้ารัน `stripe listen` แล้วได้ข้อความว่า *"stripe is not recognized"* แปลว่ายังไม่ได้ติดตั้ง Stripe CLI

**วิธีที่ 1: ใช้ Scoop (Windows)**

ตาม [Stripe CLI - GitHub](https://github.com/stripe/stripe-cli) ต้องเพิ่ม bucket ก่อน แล้วค่อยติดตั้ง:

```powershell
scoop bucket add stripe https://github.com/stripe/scoop-stripe-cli.git
scoop install stripe
```

**วิธีที่ 2: ดาวน์โหลดโดยตรง**

1. ไปที่ [Stripe CLI - Releases](https://github.com/stripe/stripe-cli/releases)
2. ดาวน์โหลดไฟล์สำหรับ Windows (เช่น `stripe_X.X.X_windows_x86_64.zip`)
3. แตก zip แล้วเอา `stripe.exe` ไปไว้ในโฟลเดอร์ที่อยู่ใน PATH (เช่น `C:\Windows` หรือสร้างโฟลเดอร์แล้วเพิ่มใน PATH)
4. เปิด PowerShell ใหม่ แล้วรัน `stripe login` (ครั้งแรกต้องล็อกอิน Stripe)
5. จากนั้นรัน:  
   `stripe listen --forward-to localhost:8000/api/payment-callback/webhook/stripe`

**วิธีที่ 3: ใช้ผ่าน npx (ถ้ามี Node.js)**

```powershell
npx stripe listen --forward-to localhost:8000/api/payment-callback/webhook/stripe
```

หลังรัน `stripe listen` แล้ว จะมีค่า `whsec_...` แสดงใน terminal — เอาไปใส่ใน `STRIPE_WEBHOOK_SECRET` ใน config.ini

## ปัญหา: Stripe Dashboard แสดง 403 Forbidden ตอนส่ง webhook

เมื่อใช้ **ngrok แบบฟรี** บ่อยครั้ง Stripe จะส่ง webhook ไม่ถึง API เพราะ ngrok จะตอบ **403 Forbidden** ให้ request ที่ไม่ใช่เบราว์เซอร์ (เช่น request จากเซิร์ฟเวอร์ Stripe)

**ทางแก้:**

- **ใช้ Stripe CLI (แนะนำสำหรับ local):**  
  `stripe listen --forward-to localhost:8000/api/payment-callback/webhook/stripe`  
  (ต้องติดตั้ง Stripe CLI ก่อน — ดูหัวข้อ "ติดตั้ง Stripe CLI (Windows)" ด้านบน)  
  Stripe CLI จะส่ง webhook ไปที่ localhost โดยตรง ไม่ผ่าน ngrok จึงไม่มี 403
- **ใช้ ngrok แผนจ่าย:** ตั้งค่า Edge ให้เพิ่ม header `ngrok-skip-browser-warning: true` หรือใช้ config `request_header.add`
- **ใช้ tunnel อื่น:** เช่น cloudflared (`cloudflared tunnel --url http://localhost:8000`) แล้วใช้ URL ที่ได้เป็น Webhook URL ใน Stripe

ดูรายละเอียดเพิ่มใน `INSTALL.md` หัวข้อ "Stripe ส่ง webhook ไม่ได้ (403 Forbidden)"

## ระบบใช้ Stripe API (ngrok / domain) เป็นหลัก

โปรเจกต์ตั้งค่าให้รับ webhook ผ่าน **Stripe API** — ลงทะเบียน **Webhook URL สาธารณะ** ใน Stripe Dashboard (Developers → Webhooks) แล้ว Stripe จะส่ง event ตรงไปที่ URL นั้น

**ขั้นตอนเมื่อใช้ ngrok:**
1. รัน ngrok (หรือ tunnel อื่นที่ได้ HTTPS) แล้วได้ URL เช่น `https://xxxx.ngrok-free.app`
2. ตั้ง `BACKEND_URL` ใน config.ini ให้ตรงกับ URL นี้ (หรือใช้ค่าที่แอปอ่านได้)
3. ไปที่ [Stripe Dashboard → Webhooks](https://dashboard.stripe.com/webhooks) → **Add endpoint**
4. **Endpoint URL:** `https://xxxx.ngrok-free.app/api/payment-callback/webhook/stripe` (แทนด้วย URL จริง)
5. เลือก Events อย่างน้อย **payment_intent.succeeded** → Add endpoint
6. Copy **Signing secret** (whsec_...) จาก endpoint ที่สร้าง → ใส่ใน `config.ini` ที่ `STRIPE_WEBHOOK_SECRET`
7. ตั้ง `STRIPE_WEBHOOK_CHANNEL=ngrok` (ค่า default ของโปรเจกต์)
8. Restart backend

**เมื่อใช้โดเมนจริง (production):** ตั้ง `STRIPE_WEBHOOK_CHANNEL=custom` และ `STRIPE_WEBHOOK_URL=https://your-domain.com/api/payment-callback/webhook/stripe` แล้วลงทะเบียน URL นี้ใน Stripe Dashboard เช่นกัน

**ทางเลือกสำหรับ dev (ไม่ต้องมี URL สาธารณะ):** ใช้ `STRIPE_WEBHOOK_CHANNEL=stripe_cli` แล้วรัน `stripe listen --forward-to http://localhost:8000/api/payment-callback/webhook/stripe` — ไม่ต้องเพิ่ม endpoint ใน Dashboard (ใช้ secret จาก terminal)

## ปัญหา: จ่าย PromptPay เสร็จแล้วแต่ระบบไม่อัปเดต (Order ไม่เป็น paid / DB ไม่เปลี่ยน)

**สาเหตุ:** Webhook จาก Stripe ไม่ถึงแอป ดังนั้น `payment_intent.succeeded` ไม่ถูกประมวลผล → ไม่มีการอัปเดต Order / back transaction

**ตรวจสอบเมื่อใช้ Stripe API (ngrok / custom):**
- **BACKEND_URL** ต้องตรงกับ URL ที่ลงทะเบียนใน Stripe Dashboard (เช่น https://xxxx.ngrok-free.app) ถ้าใช้ ngrok
- ใน **Stripe Dashboard → Webhooks** endpoint ต้องชี้ไปที่ URL ที่ backend รับได้จริง (ถ้า ngrok restart แล้ว URL เปลี่ยน ต้องแก้ endpoint ใน Dashboard ให้ชี้ URL ใหม่ และอัปเดต signing secret ถ้า Stripe ออกใหม่)
- **STRIPE_WEBHOOK_SECRET** ใน config ต้องตรงกับ Signing secret ของ endpoint ใน Dashboard
- **STRIPE_WEBHOOK_CHANNEL** = `ngrok` หรือ `custom` (ไม่ใช่ stripe_cli ถ้าไม่ได้รัน stripe listen)

เมื่อ webhook ถึงแอปแล้ว ระบบจะ: บันทึก back transaction, อัปเดต Order เป็น paid ถ้า ref2 = order_id, อัปเดต signage

## หมายเหตุ

- เวลาใช้ ngrok ใหม่ (restart) URL จะเปลี่ยน → ต้องไปแก้ **Webhook endpoint URL ใน Stripe Dashboard** ให้ชี้ URL ใหม่ และ copy **Signing secret** ใหม่ใส่ใน `STRIPE_WEBHOOK_SECRET`
- ถ้าใช้ **stripe_cli** (ทางเลือก): ค่า whsec_... จาก `stripe listen` ใส่ใน `STRIPE_WEBHOOK_SECRET` และไม่ต้องเพิ่ม endpoint ใน Dashboard
