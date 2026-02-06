# Payment Gateway – ตัวเลือกผู้ให้บริการ

ใน Admin → แท็บ **Banking** สามารถเลือก **ผู้ให้บริการ (Payment Gateway)** ได้ดังนี้

| ตัวเลือก | ผู้ให้บริการ | เอกสาร / Dashboard |
|----------|----------------|---------------------|
| **K API** | ธนาคารกสิกรไทย | K API Portal (apiportal.kasikornbank.com) |
| **SCB Deeplink** | ธนาคารไทยพาณิชย์ | [SCB Developer](https://developer.scb/) |
| **Omise QR PromptPay** | Omise | [Dashboard](https://dashboard.omise.co), [Docs PromptPay](https://docs.omise.co/promptpay) |
| **MPay QR PromptPay** | AIS (mPAY) | ติดต่อขอ API: mPAY-Followup@ais.co.th หรือ 02-078-9299 |
| **Stripe QR PromptPay** | Stripe | [Dashboard](https://dashboard.stripe.com), [Docs PromptPay](https://docs.stripe.com/payments/promptpay) |

---

## การตั้งค่าใน Admin

1. ไปที่ **Admin** → แท็บ **Banking** (หรือ Payment Gateway)
2. กด **เพิ่ม Payment Gateway Profile**
3. เลือก **ผู้ให้บริการ** จาก dropdown
4. กำหนด **Scope** (Group / Site / Store) และ ID ที่ตรงกับร้าน
5. กรอกค่าตามผู้ให้บริการที่เลือก (API Key, Secret, Webhook URL ฯลฯ)
6. ลงทะเบียน **Webhook URL** กับผู้ให้บริการตามลิงก์ในกล่อง "Link Webhook สำหรับลงทะเบียน"

---

## Webhook URLs (แยกตามผู้ให้บริการ)

| ผู้ให้บริการ | URL สำหรับลงทะเบียน |
|--------------|----------------------|
| SCB | `{BACKEND_URL}/api/payment-callback/webhook` |
| K Bank | `{BACKEND_URL}/api/payment-callback/webhook/kbank` |
| Omise | `{BACKEND_URL}/api/payment-callback/webhook/omise` |
| Stripe | `{BACKEND_URL}/api/payment-callback/webhook/stripe` |

- **Omise**: ลงทะเบียนที่ [Dashboard Omise](https://dashboard.omise.co) → Webhooks  
  Event: `charge.complete`  
  ต้องส่ง `metadata.ref1` = store token (20 หลัก) ตอนสร้าง charge

- **Stripe**: ลงทะเบียนที่ [Dashboard Stripe](https://dashboard.stripe.com/webhooks)  
  Event: `payment_intent.succeeded`  
  ต้องส่ง `metadata.ref1` = store token ตอนสร้าง PaymentIntent

---

## การสร้าง QR ผ่าน Gateway (Omise / Stripe)

เมื่อตั้งค่า Profile เป็น **Omise** หรือ **Stripe** สำหรับร้านนั้นแล้ว สามารถเรียก:

- **POST** `/api/payment-callback/stores/{store_id}/create-gateway-qr`  
  Body: `{ "amount": 100 }` (บาท)

ระบบจะ resolve profile ของร้าน → สร้าง Omise Charge หรือ Stripe PaymentIntent โดยใส่ `metadata.ref1 = store.token` แล้วคืนค่า QR image (Omise) หรือ `client_secret` (Stripe) ให้ Store-POS/Signage ใช้แสดง QR ได้

---

## MPay (AIS)

mPAY เป็นช่องทางชำระของ AIS รองรับหลายวิธี รวมถึง QR / PromptPay  
การเชื่อมต่อ API ต้อง **ติดต่อทีม mPAY โดยตรง** เพื่อขอ Merchant API และเอกสารเทคนิค:

- อีเมล: **mPAY-Followup@ais.co.th**
- โทร: **02-078-9299**
- เว็บ: [mpay.th](https://www.mpay.th/en/)

ในระบบได้เตรียมฟิลด์ตั้งค่า (Merchant ID, API Key, Webhook Secret) ไว้แล้ว เมื่อได้ API จาก AIS สามารถเพิ่ม service และ webhook handler ในโค้ดให้ตรงกับเอกสารของ mPAY ได้
