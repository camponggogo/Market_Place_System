# Stripe Webhook: ระบบใช้ Stripe API (ngrok / domain) เป็นหลัก

โปรเจกต์นี้รับ Stripe webhook ผ่าน **Stripe API** — ลงทะเบียน **Webhook URL สาธารณะ** ใน Stripe Dashboard แล้ว Stripe ส่ง event ตรงไปที่ URL นั้น ช่องทางกำหนดใน `config.ini` ด้วย `STRIPE_WEBHOOK_CHANNEL`:

| ค่า | ความหมาย | ใช้เมื่อไหร่ |
|-----|-----------|----------------|
| **ngrok** | ใช้ **URL จาก BACKEND_URL** (เช่น `https://xxx.ngrok-free.app`) ลงทะเบียนใน Stripe Dashboard | ทดสอบด้วย ngrok หรือ tunnel ที่ได้ HTTPS (ค่า default) |
| **custom** | ใช้ **URL จาก STRIPE_WEBHOOK_URL** (โดเมนจริง หรือ tunnel ที่มี HTTPS) | Production (VPS, Docker, cloud) ที่มี HTTPS |
| **stripe_cli** | รับ event ผ่านคำสั่ง `stripe listen` แล้วส่งต่อมา **localhost** | ทางเลือกสำหรับ dev บนเครื่องตัวเองเท่านั้น (ไม่ต้องมี URL สาธารณะ) |

---

## Stripe API (ngrok / custom) — ช่องทางหลักของโปรเจกต์

- **การทำงาน:** ลงทะเบียน **Webhook URL สาธารณะ** ใน Stripe Dashboard (Developers → Webhooks) เช่น `https://your-domain.com/api/payment-callback/webhook/stripe` หรือ `https://xxxx.ngrok-free.app/api/payment-callback/webhook/stripe` → Stripe ส่ง POST ตรงไปที่ URL นั้น
- **ต้องมี HTTPS** — Stripe กำหนดให้ webhook endpoint ใช้ HTTPS
- **Webhook secret:** ได้จาก Stripe Dashboard หลังสร้าง endpoint (Reveal signing secret) → ใส่ใน `STRIPE_WEBHOOK_SECRET`
- **ngrok:** ตั้ง `STRIPE_WEBHOOK_CHANNEL=ngrok` และให้ `BACKEND_URL` ตรงกับ URL ของ ngrok; ลงทะเบียน `{BACKEND_URL}/api/payment-callback/webhook/stripe` ใน Dashboard (แผนฟรีอาจได้ 403 — ดู INSTALL.md)
- **custom:** ตั้ง `STRIPE_WEBHOOK_CHANNEL=custom` และ `STRIPE_WEBHOOK_URL=https://...` ใช้กับโดเมนจริงหรือ tunnel ที่มี HTTPS สำหรับ production

## Stripe CLI — ทางเลือกสำหรับ dev เท่านั้น

- **การทำงาน:** รัน `stripe listen --forward-to http://localhost:8000/api/payment-callback/webhook/stripe` บนเครื่องที่รันแอป → CLI รับ event แล้วส่ง POST มาที่ localhost
- **ไม่ต้องลงทะเบียน URL ใน Stripe Dashboard**
- **Webhook secret:** ใช้ค่าที่ `stripe listen` แสดงใน terminal (whsec_...); ใส่ใน `STRIPE_WEBHOOK_SECRET` (ค่าเปลี่ยนทุกครั้งที่รัน `stripe listen` ใหม่)
- **ข้อจำกัด:** ต้องรัน Stripe CLI บนเครื่องเดียวกับ backend; เหมาะแค่ development บนเครื่องตัวเอง

---

## สรุปสั้น ๆ

| | Stripe API (ngrok / custom) — ใช้เป็นหลัก | Stripe CLI — ทางเลือกสำหรับ dev |
|---|-------------------------------------------|----------------------------------|
| ลงทะเบียน URL ใน Dashboard | **ต้อง** (URL สาธารณะ เช่น ngrok หรือโดเมน) | ไม่ต้อง |
| HTTPS ของ endpoint | **จำเป็น** | ไม่จำเป็น (CLI ส่งมา localhost) |
| รันที่ไหน | ใช้ได้ทั้ง dev (ngrok) และ production (custom) | เครื่อง dev เท่านั้น (เดียวกับ backend) |
| ค่า default ในโปรเจกต์ | `STRIPE_WEBHOOK_CHANNEL=ngrok` | ตั้งเป็น `stripe_cli` ได้ถ้าต้องการ |

---

## Deploy บน Cloud Docker และไม่มี SSL (ทำ HTTPS ไม่ได้ที่ตัว server)

ถ้า **server ไม่มี SSL** (ไม่มี HTTPS) โดยตรง:

- Stripe **ส่ง webhook ได้เฉพาะ HTTPS** (หรือ localhost ผ่าน Stripe CLI)
- ดังนั้น **ถ้าแอปอยู่หลัง http:// เท่านั้น โดยไม่มีอะไรทำ HTTPS ด้านหน้า จะลงทะเบียน webhook URL แบบ Stripe API ไม่ได้**

ทางเลือกที่เหมาะ:

### 1. ให้มี HTTPS ด้านหน้าแอป (แนะนำสำหรับ production)

เพิ่ม layer ที่ออก SSL ให้ก่อนถึงแอป แล้วใช้ **Stripe API (custom)**:

- **แบบ A: Reverse proxy ใน Docker (Caddy + Let's Encrypt)**  
  - เพิ่ม service Caddy ใน docker-compose รับพอร์ต 443 และขอ certificate อัตโนมัติ (ต้องมีโดเมนชี้มาที่ server)  
  - ตั้ง `BACKEND_URL=https://your-domain.com` และลงทะเบียน webhook ใน Stripe เป็น `https://your-domain.com/api/payment-callback/webhook/stripe`  
  - ใน config: `STRIPE_WEBHOOK_CHANNEL=custom` และ `STRIPE_WEBHOOK_URL=https://your-domain.com/api/payment-callback/webhook/stripe`

- **แบบ B: Cloudflare Tunnel (cloudflared)**  
  - รัน cloudflared บน server หรือใน Docker ให้ tunnel ออกไปที่ Cloudflare จะได้ **HTTPS URL** (เช่น `https://your-app.cfargotunnel.com`)  
  - ลงทะเบียน URL นี้ใน Stripe แล้วใช้ `STRIPE_WEBHOOK_CHANNEL=custom` และ `STRIPE_WEBHOOK_URL=https://your-app.../api/payment-callback/webhook/stripe`  
  - ไม่ต้องเปิดพอร์ต 443 ที่ server; ไม่ต้องมี SSL ที่ server เอง

- **แบบ C: SSL จาก Cloud / Load Balancer**  
  - ถ้าใช้ cloud provider ที่มี Load Balancer หรือ API Gateway ที่ออก SSL ให้ ใช้ URL ที่ได้นั้นเป็น webhook URL และตั้งค่าแบบ custom เหมือนด้านบน

### 2. ใช้ Stripe CLI บน server (ทางเลือกชั่วคราว ไม่แนะนำสำหรับ production)

- รัน `stripe listen --forward-to http://localhost:8000/api/payment-callback/webhook/stripe` **บน server** (ใน container หรือข้างๆ container ที่รันแอป)
- ใส่ secret จาก `stripe listen` ลงใน config และตั้ง `STRIPE_WEBHOOK_CHANNEL=stripe_cli`
- **ข้อเสีย:** ต้องรัน Stripe CLI ค้างไว้; พอ restart `stripe listen` secret เปลี่ยน ต้องอัปเดต config และอาจพลาด event ตอน restart

เหมาะแค่กรณีทดสอบหรือรันชั่วคราวบน server ที่ยังไม่มี HTTPS

### 3. สรุปสำหรับ Cloud Docker ที่ไม่มี SSL

- **ถ้าต้องการ production จริง:** ควรทำให้มี **HTTPS** ด้านหน้าแอป (Caddy + Let's Encrypt, Cloudflare Tunnel หรือ SSL จาก cloud) แล้วใช้ **Stripe API (custom)** ลงทะเบียน webhook เป็น HTTPS
- **ถ้าชั่วคราวยังไม่มี HTTPS:** ใช้ **Stripe CLI** บน server เป็นทางเลือกได้ แต่ต้องยอมรับข้อจำกัดด้านการ restart และการดูแล secret

ในโปรเจกต์นี้ค่าที่เกี่ยวข้องอยู่ใน `config.ini`:

- `STRIPE_WEBHOOK_CHANNEL` = `stripe_cli` | `ngrok` | `custom`
- `STRIPE_WEBHOOK_URL` = ใช้เมื่อเป็น `custom` (ต้องเป็น URL เต็มถึง path webhook และต้องเป็น **https**)
