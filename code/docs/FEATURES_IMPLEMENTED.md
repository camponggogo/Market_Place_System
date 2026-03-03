# สรุปฟีเจอร์ที่ทำ (ตามที่ร้องขอ)

## สรุปส่วนที่ทำเต็ม (รอบล่าสุด)

### หน้า Admin – จัดการคูปอง
- **/admin/coupon** – ออก E-Coupon ใหม่ (จำนวนเงิน, วิธีชำระ, กำหนดให้ลูกค้า), กำหนด E-Coupon ให้ลูกค้า, รายการ E-Coupon (กรองตามสถานะ: ว่าง/กำหนดแล้ว/ใช้แล้ว)

### หน้า Admin – ตั้งค่าการรับเงิน
- **/admin/payment-settings** – หน้ารวมลิงก์ไปแท็บ Banking ใน Admin หลัก + แสดงรายการ Payment Gateway (Banking Profiles) ที่มีอยู่

### หน้า Admin – ปฏิทิน Campaign / โปรโมชั่น
- **/admin/calendar** – ปฏิทินแบบเดือน แสดงเหตุการณ์จาก **โฆษณา (ad_feeds)** และ **โปรโมชั่นร้าน (store_promotions)** ตาม start_at/end_at, valid_from/valid_to; มี API `/api/admin/ads/calendar/events` และ API จัดการโปรโมชั่น `/api/admin/ads/promotions` (list, create, update)

### หน้า Admin – สรุปผลการตอบรับโฆษณา
- **/admin/ads-summary** – สรุปจำนวน View และ Click ต่อโฆษณา (กรองช่วงวันที่); ใช้ตาราง **ad_impressions** (บันทึกเมื่อสมาชิกดู/กดโฆษณา)
- **Member** – เมื่อโหลดโฆษณาใน dashboard จะเรียก `POST /api/member/ads/track` (event_type: view); เมื่อกดลิงก์โฆษณาจะส่ง event_type: click

### ฐานข้อมูล
- **ad_impressions** – ad_feed_id, event_type (view/click), customer_id (optional), created_at
- Migration: `scripts/migrate_audit_menu.py` (สร้างตาราง ad_impressions)

---

## หน้า Member
- **Stripe เป็นตัวเลือกการจ่าย** รองรับ PromptPay, e-Wallet (TrueWallet), บัตรเครดิต/เดบิต ผ่าน Stripe
- **ปุ่มเติมเงิน** เลือกวิธีชำระ: Prompt Pay | e-Wallet | บัตรเครดิต/เดบิต
- **ระบบรับจ่ายเงิน** เติมเงิน/ซื้อ E-Coupon ผ่าน Stripe (Webhook อัปเดตยอด); ประวัติใน Member Activity
- **รายการใช้จ่าย/เติมเงิน** แสดงตารางประวัติเต็มใน dashboard (จาก `/api/member/activities`)

## หน้า Admin
- **รายการสำรองฉุกเฉิน** หน้ากรอกข้อมูลการนำเข้ารายการขาย/แลกเปลี่ยน/อื่นๆ กรณีไฟดับ ระบบล่ม (`/emergency-backup`) – บังคับล็อกอิน; **ดูย้อนหลังได้เฉพาะ admin**
- **Audit Logs** เก็บทุกการดำเนินการ (`/audit-logs`) – เฉพาะ admin; API `/api/audit-logs`
- **จัดการโฆษณา (Ads)** มี `store_id` (null = ทุกร้าน), `start_at`, `end_at` ตั้งเวลาปล่อยได้; API `/api/admin/ads/list` create/update รองรับฟิลด์ใหม่
- จัดการคูปอง/E-Coupon อยู่ที่ API เดิม (`admin_ecoupon`)

## Store POS
- **เมนูและ Add-on** หน้า store-menus ใช้ API เดิม; **เมื่อแก้ไขราคา (unit_price/addon_options)** ระบบจะ:
  - บันทึกราคาเดิมลง `menu_price_logs` เพื่ออ้างอิงรายการย้อนหลัง
  - บันทึก audit log (`menu_update`)
- **หน้ากรอกข้อมูลสำรอง** ใช้หน้า `/emergency-backup` (ล็อกอิน Store POS หรือ Admin ได้); ดูย้อนหลังเฉพาะ admin
- **ระบบ logs** ทุกการดำเนินการที่เกี่ยวข้องบันทึกลง `audit_logs` (source: store_pos / admin / system)

## ฐานข้อมูล / Migration
- `scripts/migrate_audit_menu.py`: เพิ่ม `audit_logs.source`, `users.is_admin`, `emergency_backup_entries`, `menu_price_logs`, `ad_feeds.store_id`, `ad_feeds.start_at`, `ad_feeds.end_at`
- `scripts/seed_store_pos_user.py`: สร้าง user `admin` / `admin123` เป็น admin (is_admin=True)

## การใช้งาน
- **STRIPE_WEBHOOK_SECRET** ใส่ใน `config.ini` ตาม `docs/STRIPE_NGROK.md` เมื่อใช้ ngrok ทดสอบ Webhook
- ล็อกอิน Admin: ใช้ user `admin` / `admin123` (หลัง seed) เพื่อเข้า `/emergency-backup`, `/audit-logs` และดูรายการย้อนหลัง
