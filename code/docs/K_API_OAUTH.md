# K Bank (K API) – IDENTITY และ OAuth 2.0

อ้างอิงจาก K API Portal ธนาคารกสิกร และข้อมูลใน **K_API.note**:

- [Inward Remittance - Documentation IDENTITY](https://apiportal.kasikornbank.com/product/public/Fund%20Transfer/Inward%20Remittance/Documentation/IDENTITY)
- [Inward Remittance - Try API OAuth 2.0](https://apiportal.kasikornbank.com/product/public/Fund%20Transfer/Inward%20Remittance/Try%20API/OAuth%202.0)

## IDENTITY (การระบุตัวตนแอป)

จาก **K_API.note** ใช้ค่าต่อไปนี้เป็นตัวระบุแอปกับ K API:

| ค่าใน K_API.note | ความหมาย | ใช้ใน OAuth |
|------------------|-----------|-------------|
| **CUSTOMER ID**  | รหัสลูกค้า/แอป (client_id) | ส่งร่วมกับ Consumer Secret ใน Basic Auth |
| **CONSUMER SECRET** | รหัสลับของแอป (client_secret) | ส่งร่วมกับ Customer ID ใน Basic Auth |
| ISSUED / EXPIRES | วันที่ออก / หมดอายุ (ถ้ามี) | ใช้ตรวจสอบอายุการใช้งานแอป |

ในโปรเจกต์นี้:
- เก็บใน **config**: `[K_API]` → `KBANK_CUSTOMER_ID`, `KBANK_CONSUMER_SECRET`
- เก็บต่อร้านใน **Store**: `kbank_customer_id`, `kbank_consumer_secret` (ถ้าต้องการแยกแอปต่อร้าน)

## OAuth 2.0 (Client Credentials)

ขั้นตอนขอ Access Token ตาม Try API OAuth 2.0:

1. **Endpoint (Sandbox)**  
   `POST https://dev.openapi-nonprod.kasikornbank.com/v2/oauth/token`

2. **Header**  
   - `Authorization: Basic <base64(CUSTOMER_ID:CONSUMER_SECRET)>`  
   - `Content-Type: application/x-www-form-urlencoded`

3. **Body**  
   - `grant_type=client_credentials`

4. **ตัวอย่าง Response (จาก K_API.note)**  
   - `token_type`: Bearer  
   - `access_token`: ใช้ใส่ Header `Authorization: Bearer <access_token>` เวลาเรียก API อื่น (เช่น Inward Remittance)  
   - `expires_in`: จำนวนวินาที (เช่น 1799)

## การใช้ในโปรเจกต์

- **Config**: `code/config.ini` → `[K_API]` ใส่ค่าจาก K_API.note  
- **Service**: `app.services.kbank_oauth.get_access_token()`  
  - อ่าน Customer ID / Consumer Secret จาก config (หรือส่งเข้าไป)  
  - ส่ง Basic Auth + `grant_type=client_credentials` ไปที่ token URL  
  - cache token จนใกล้หมดอายุ แล้วคืน `access_token`  
- **เรียก K API อื่น**: ใช้ Header `Authorization: Bearer <access_token>` ที่ได้จาก `get_access_token()`

## ตัวอย่าง curl (จาก K_API.note)

```bash
curl --silent --location --request POST 'https://dev.openapi-nonprod.kasikornbank.com/v2/oauth/token' \
  --header 'Authorization: Basic <base64(CUSTOMER_ID:CONSUMER_SECRET)>' \
  --data-urlencode 'grant_type=client_credentials'
```

ในโปรเจกต์เราใช้ค่าจาก **K_API.note** ผ่าน config และ `kbank_oauth.get_access_token()` แทนการส่ง curl เอง
