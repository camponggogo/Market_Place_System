# ระบบลูกค้าสมาชิกออนไลน์ (Member Online)

## สรุปฟีเจอร์

- **ระบบจัดการลูกค้า** รองรับมือถือ (Mobile responsive)
- **หน้าลงทะเบียน (Register)** เก็บ: ชื่อผู้ใช้ (4 ตัวขึ้นไป), หมายเลขโทรศัพท์, รหัสผ่าน, อีเมล (ถ้ามี), ชื่อ (ถ้ามี)
- **หน้าแรก Login** ช่องกรอก: ชื่อผู้ใช้ หรือ เบอร์โทร หรือ อีเมล + รหัสผ่าน มีลิงก์ไปหน้า register
- **หลัง Login** แดชบอร์ดเดียว: ข้อมูลส่วนตัวย่อ, ยอดเงินคงเหลือ, คูปอง, โปรโมชั่น, แต้มสะสม, E-Coupon
- **เมนูล่าง (Footer)** ไอคอน: หน้าหลัก | คะแนนสะสม | **สแกนจ่าย (กลาง)** | ประวัติการใช้งาน | ข้อมูลสมาชิก
- **E-Coupon จาก Admin** แลกด้วยเงินสด, PromptPay, Credit/Debit, E-money (Omise, Stripe, Alipay, WeChat, Line Pay, True Wallet)
- **สแกน QR PromptPay** อ่าน plain text ดึง store_id, order_id หักจ่ายด้วย E-Coupon; เปิดกล้องมือถือ อนุญาตครั้งเดียวเก็บไว้ใช้ครั้งต่อไป
- **ฐานข้อมูล** ลูกค้า + แต้มสะสม, Voucher, โปรโมชั่นร้าน (Admin กำหนด), E-Coupon, Ad Feed, ประวัติการใช้งาน/เติมเงิน/จ่ายเงิน
- **ฟีดโฆษณา** แสดงในหน้าสมาชิก (Admin จัดการ)
- **รองรับ Line OA** เปิดหน้าเว็บใน Line ได้ (viewport + responsive)

## URL หลัก

| หน้าที่ | URL |
|--------|-----|
| Login (หน้าแรกสมาชิก) | `/member` |
| ลงทะเบียน | `/member/register` |
| แดชบอร์ด (หลังล็อกอิน) | `/member/dashboard` |
| สแกนจ่าย E-Coupon | `/member/scan` |

## API

- `POST /api/member/register` – ลงทะเบียน (username 4+, phone, password, email optional)
- `POST /api/member/login` – ล็อกอิน (login_id = username หรือ phone หรือ email, password) คืน JWT
- `GET /api/member/me` – ข้อมูลแดชบอร์ด (ต้องส่ง Header: Authorization: Bearer &lt;token&gt;)
- `GET /api/member/ads` – รายการโฆษณา
- `GET /api/member/activities` – ประวัติการใช้งาน
- `POST /api/member/scan-pay` – จ่ายด้วย E-Coupon (body: qr_text หรือ store_id, order_id, amount)
- `POST /api/admin/ecoupon/issue` – ออก E-Coupon (amount, payment_method, customer_id optional)
- `GET /api/admin/ecoupon/list` – รายการ E-Coupon
- `POST /api/admin/ecoupon/assign` – กำหนด E-Coupon ให้ลูกค้า
- `GET /api/admin/ads/list` – รายการโฆษณา (Admin)
- `POST /api/admin/ads/create` – สร้างโฆษณา
- `PUT /api/admin/ads/{id}` – แก้ไข
- `DELETE /api/admin/ads/{id}` – ลบ

## Migration

รันครั้งเดียวหลังอัปเดตโค้ด:

```bash
cd code
python scripts/migrate_member_online.py
```

## การใช้ใน Line OA

- ใส่ URL หน้าเว็บเป็น `https://your-domain/member` ในเมนูหรือ Rich Menu
- ลูกค้าเปิดใน Line in-app browser ได้เลย หน้าเว็บรองรับ viewport มือถือ
- ถ้าต้องการผูก Line user กับสมาชิก ใช้ `line_user_id` ในตาราง `customers` (มีอยู่แล้ว) อัปเดตเมื่อลูกค้า bind กับ Line
