# การตรวจสอบ Stripe + QR PromptPay (Member & Store-POS)

## สรุปการตั้งค่าและ Flow

### 1. Config (config.ini เท่านั้น)
- **STRIPE_SECRET_KEY**, **STRIPE_PUBLISHABLE_KEY**, **STRIPE_WEBHOOK_SECRET** อยู่ใน `code/config.ini` [STRIPE]
- Store-POS ใช้ Stripe ได้แม้ไม่มี Banking Profile: ใช้ค่าจาก config เป็น fallback

### 2. Member (เติมเงิน / ซื้อ E-Coupon)
- **stripe-config**: `GET /api/member/stripe-config` → คืน `publishableKey` จาก config
- **create-payment-intent**: `POST /api/member/stripe/create-payment-intent` (amount, intent_type, payment_method)
  - payment_method: `promptpay` | `card` | `truewallet` (truewallet ใช้ promptpay แทนถ้าไม่ได้เปิดใน Stripe)
  - สร้าง PaymentIntent แล้วคืน `client_secret`
- **Frontend**: โหลด Stripe.js → mount Payment Element ที่ `#topup-payment-element` ด้วย client_secret → แสดง QR PromptPay
- **ยืนยันชำระ**: กดปุ่ม → `elements.submit()` แล้ว `stripe.confirmPayment()`
- **Webhook**: เมื่อชำระสำเร็จ Stripe ส่ง `payment_intent.succeeded` → ระบบอัปเดตยอด Member / E-Coupon

### 3. Store-POS (PromptPay QR)
- **gateway-info**: `GET /api/payment-callback/stores/{id}/gateway-info`
  - ลำดับ: Stripe (จาก Banking Profile หรือจาก config) → Omise → SCB Deeplink
  - คืน `provider`, `stripe_publishable_key` (เมื่อใช้ Stripe)
- **สร้าง QR**:
  - ถ้า provider = stripe: เรียก `POST .../create-gateway-qr` → ได้ `client_secret` → mount Stripe Payment Element ใน modal (และโหลด QR เดิมจาก generate-promptpay-qr สำหรับเปรียบเทียบ)
  - ถ้า omise/scb_deeplink: เรียก create-gateway-qr → ได้ qr_image
  - ถ้าไม่มี gateway: เรียก `POST /api/stores/{id}/generate-promptpay-qr` → ได้ qr_code_tag30 (EMV)
- **create-gateway-qr**: รองรับใช้ Stripe จาก config เมื่อร้านไม่มี Banking Profile (use_global_stripe)
- **Webhook**: payment_intent.succeeded มี metadata.ref1 (store token), ref2 (order_id) → บันทึก promptpay_back_transactions และอัปเดต Order เป็น paid

### 4. ขนาด QR ให้สแกนง่าย
- **Backend**: สร้างรูป QR ที่ 360x360 px (เดิม 300) ใน `promptpay.py` และ `stores.py`
- **Store-POS modal**: รูป QR มี min 280px, max 380px, พื้นหลังขาว, object-fit: contain
- **Store-POS Stripe slot**: container สูงอย่างน้อย 320px
- **Member**: container Payment Element สูงอย่างน้อย 340px, iframe ขั้นต่ำ 320px
- **Signage**: รูป QR ขั้นต่ำ 220px, สูงสุด 360px

## Checklist การทดสอบ

- [ ] Member: เลือก PromptPay → ใส่จำนวน → ดำเนินการเติมเงิน → เห็น QR จาก Stripe และสแกนได้
- [ ] Member: เลือกบัตร → กรอกบัตร → ยืนยันชำระ
- [ ] Store-POS: ร้านมี Stripe (จาก Profile หรือ config) → กด PromptPay → เห็น QR (Stripe + QR เดิมถ้าใช้ Stripe)
- [ ] Store-POS: ร้านไม่มี gateway → กด PromptPay → เห็น QR EMV จาก generate-promptpay-qr
- [ ] ลงทะเบียน Webhook URL ใน Stripe Dashboard และใส่ STRIPE_WEBHOOK_SECRET ใน config.ini
- [ ] หลังชำระ (Member หรือ Store) ตรวจสอบว่า Webhook อัปเดตยอด/Order ถูกต้อง
