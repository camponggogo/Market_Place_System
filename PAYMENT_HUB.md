# Payment Hub System - ระบบจัดการการชำระเงินหลายรูปแบบ

## ภาพรวมระบบ

Payment Hub เป็นระบบกลางสำหรับจัดการการชำระเงินหลายรูปแบบ โดยแยกออกเป็น 2 รูปแบบการทำงาน:

### รูปแบบที่ 1: เงินสดเท่านั้น
- ลูกค้าแลกเงินสด → Food Court ID ที่ Counter
- ระบุจำนวนเงิน → ได้ Food Court ID
- ร้านค้าตั้งราคารอ → รับ Food Court ID → หักยอดเงิน
- ลูกค้ารับเงินที่เหลือที่ Counter

### รูปแบบที่ 2: หลายรูปแบบ
- ลูกค้าแลกเงินสด, Credit Card, PromptPay, Alipay, True Wallet, WeChat, Crypto → Food Court ID ที่ Counter
- ระบุจำนวนเงิน → ได้ Food Court ID
- ร้านค้าตั้งราคารอ → รับ Food Court ID → หักยอดเงิน
- ลูกค้ารับเงินที่เหลือที่ Counter
- สรุปยอดพร้อมระบุประเภทเงินที่รับมา

## Payment Methods ที่รองรับ

### 1. เงินสด (Cash)
- Code: `cash`
- Type: `cash`
- Gateway: ไม่ต้องใช้

### 2. บัตรเครดิต (Credit Cards)
- Visa: `credit_card_visa`
- Mastercard: `credit_card_mastercard`
- American Express: `credit_card_amex`
- JCB: `credit_card_jcb`
- UnionPay: `credit_card_unionpay`
- Type: `card`
- Gateway: ต้องใช้

### 3. Digital Wallets - ประเทศไทย
- True Wallet: `true_wallet`
- PromptPay: `promptpay`
- LINE Pay: `line_pay`
- Rabbit LINE Pay: `rabbit_line_pay`
- ShopeePay: `shopee_pay`
- GrabPay: `grab_pay`
- Type: `wallet`
- Gateway: ต้องใช้

### 4. Digital Wallets - สากล
- Apple Pay: `apple_pay`
- Google Pay: `google_pay`
- Samsung Pay: `samsung_pay`
- Alipay: `alipay`
- WeChat Pay: `wechat_pay`
- PayPal: `paypal`
- Amazon Pay: `amazon_pay`
- Venmo: `venmo` (USA)
- Zelle: `zelle` (USA)
- Cash App: `cash_app` (USA)
- Type: `wallet`
- Gateway: ต้องใช้

### 5. Bank Transfers
- Bank Transfer: `bank_transfer`
- Wire Transfer: `wire_transfer`
- Type: `bank_transfer`
- Gateway: ต้องใช้

### 6. Cryptocurrency
- Bitcoin (BTC): `crypto_btc`
- Ethereum (ETH): `crypto_eth`
- Ripple (XRP): `crypto_xrp`
- Bitkub Token: `crypto_bitkub`
- Binance Coin (BNB): `crypto_binance`
- Solana (SOL): `crypto_solana`
- Tether (USDT): `crypto_usdt`
- USD Coin (USDC): `crypto_usdc`
- Custom Token: `crypto_custom`
- Type: `crypto`
- Gateway: ต้องใช้

### 7. Points & Rewards
- The 1 Card Points: `points_the1`
- BlueCard Points: `points_bluecard`
- Credit Card Points: `points_credit_card`
- Airline Miles: `points_airline`
- Hotel Points: `points_hotel`
- Custom Points: `points_custom`
- Type: `points`
- Gateway: ต้องใช้

### 8. Vouchers & Coupons
- Voucher: `voucher`
- Gift Card: `gift_card`
- Coupon: `coupon`
- Type: `voucher`
- Gateway: ไม่ต้องใช้

### 9. Buy Now Pay Later (BNPL)
- Atome: `bnpl_atome`
- Split: `bnpl_split`
- Grab PayLater: `bnpl_grab_paylater`
- Affirm: `bnpl_affirm` (USA)
- Klarna: `bnpl_klarna`
- Afterpay: `bnpl_afterpay`
- Type: `bnpl`
- Gateway: ต้องใช้

### 10. Custom Payment
- Custom: `custom`
- Type: `custom`
- Gateway: ต้องใช้ (กำหนดเอง)

## Flow การทำงาน

### 1. การแลก Food Court ID ที่ Counter

```
POST /api/counter/exchange
{
  "amount": 1000.00,
  "payment_method": "cash",
  "payment_details": {},
  "counter_id": 1,
  "counter_user_id": 1,
  "customer_id": null  // Optional
}
```

**Response:**
```json
{
  "success": true,
  "foodcourt_id": "FC-20241201-12345",
  "amount": 1000.00,
  "payment_method": "cash",
  "created_at": "2024-12-01T10:00:00"
}
```

### 2. การใช้ Food Court ID ที่ร้านค้า

```
POST /api/payment-hub/use
{
  "foodcourt_id": "FC-20241201-12345",
  "store_id": 1,
  "amount": 250.00
}
```

**Response:**
```json
{
  "success": true,
  "foodcourt_id": "FC-20241201-12345",
  "remaining_balance": 750.00,
  "transaction_id": 123
}
```

### 3. การตรวจสอบยอดเงินคงเหลือ

```
GET /api/counter/balance/FC-20241201-12345
```

**Response:**
```json
{
  "foodcourt_id": "FC-20241201-12345",
  "initial_amount": 1000.00,
  "current_balance": 750.00,
  "status": "active",
  "payment_method": "cash",
  "created_at": "2024-12-01T10:00:00"
}
```

### 4. การคืนเงินที่เหลือที่ Counter

```
POST /api/counter/refund
{
  "foodcourt_id": "FC-20241201-12345",
  "counter_id": 1,
  "counter_user_id": 1
}
```

**Response:**
```json
{
  "success": true,
  "foodcourt_id": "FC-20241201-12345",
  "refund_amount": 750.00,
  "original_payment_method": "cash"
}
```

## รายงานสรุปยอด

### 1. สรุปยอดรายร้านค้า

```
GET /api/reports/payment/store/{store_id}?start_date=2024-12-01&end_date=2024-12-31
```

**Response:**
```json
{
  "store_id": 1,
  "period": {
    "start_date": "2024-12-01T00:00:00",
    "end_date": "2024-12-31T23:59:59"
  },
  "summary": {
    "total_transactions": 150,
    "total_amount": 37500.00
  },
  "by_payment_method": {
    "cash": {"count": 100, "amount": 25000.00},
    "promptpay": {"count": 50, "amount": 12500.00}
  }
}
```

### 2. สรุปยอดรายวัน

```
GET /api/reports/payment/daily?date=2024-12-01
```

### 3. สรุปยอดรายเดือน

```
GET /api/reports/payment/monthly?year=2024&month=12
```

### 4. สรุปยอดรายปี

```
GET /api/reports/payment/yearly?year=2024
```

## ระบบออกใบกำกับภาษี

ใบกำกับภาษีจะระบุประเภทเงินที่รับมาอัตโนมัติ:

```
POST /api/tax/invoices/{transaction_id}
```

**Response:**
```json
{
  "id": 1,
  "invoice_number": "INV-20241201-00001",
  "transaction_id": 123,
  "amount": 250.00,
  "vat_amount": 17.50,
  "total_amount": 267.50,
  "payment_method": "cash",  // ระบุประเภทเงินที่รับมา
  "tax_id": "1234567890123",
  "company_name": "Food Court Management Co., Ltd.",
  "issued_at": "2024-12-01T10:30:00"
}
```

## Database Models

### FoodCourtID
- `foodcourt_id`: Food Court ID ที่ให้ลูกค้า
- `customer_id`: ID ลูกค้า (Optional)
- `initial_amount`: จำนวนเงินที่แลกมา
- `current_balance`: ยอดเงินคงเหลือ
- `payment_method`: วิธีชำระเงิน
- `payment_details`: รายละเอียดการชำระเงิน (JSON)
- `status`: active, used, refunded, expired

### CounterTransaction
- บันทึกการแลก Food Court ID ที่ Counter
- เก็บข้อมูล: amount, payment_method, payment_details

### StoreTransaction
- บันทึกการใช้งาน Food Court ID ที่ร้านค้า
- เก็บข้อมูล: store_id, amount

### PaymentGateway
- Configuration สำหรับ Custom Payment Methods
- รองรับการสร้าง Payment Gateway ใหม่โดย Admin

## API Endpoints

### Counter APIs
- `POST /api/counter/exchange` - แลก Food Court ID
- `GET /api/counter/balance/{foodcourt_id}` - ตรวจสอบยอดเงิน
- `POST /api/counter/refund` - คืนเงินที่เหลือ
- `GET /api/counter/payment-methods` - ดึงรายการ Payment Methods

### Payment Hub APIs
- `POST /api/payment-hub/use` - ใช้ Food Court ID ที่ร้านค้า
- `GET /api/payment-hub/balance/{foodcourt_id}` - ตรวจสอบยอดเงิน

### Report APIs
- `GET /api/reports/payment/store/{store_id}` - สรุปยอดรายร้านค้า
- `GET /api/reports/payment/daily` - สรุปยอดรายวัน
- `GET /api/reports/payment/monthly` - สรุปยอดรายเดือน
- `GET /api/reports/payment/yearly` - สรุปยอดรายปี

## ตัวอย่างการใช้งาน

### Python Example

```python
from app.services.payment_hub import PaymentHub
from app.models import PaymentMethod

# แลก Food Court ID
payment_hub = PaymentHub(db)
foodcourt_id = payment_hub.exchange_to_foodcourt_id(
    amount=1000.00,
    payment_method=PaymentMethod.CASH,
    counter_id=1,
    counter_user_id=1
)

# ใช้ที่ร้านค้า
result = payment_hub.use_foodcourt_id(
    foodcourt_id_str=foodcourt_id.foodcourt_id,
    store_id=1,
    amount=250.00
)

# คืนเงินที่เหลือ
refund = payment_hub.refund_remaining_balance(
    foodcourt_id_str=foodcourt_id.foodcourt_id,
    counter_id=1,
    counter_user_id=1
)
```

## หมายเหตุ

1. **Food Court ID Format**: `FC-YYYYMMDD-XXXXX`
2. **Status Flow**: `active` → `used` / `refunded`
3. **Payment Details**: เก็บเป็น JSON สำหรับข้อมูลเพิ่มเติม (เช่น card number, transaction ID)
4. **Tax Invoice**: ระบุประเภทเงินที่รับมาอัตโนมัติจาก Payment Method
5. **Reports**: รองรับการสรุปยอดตาม Payment Method และ Store

