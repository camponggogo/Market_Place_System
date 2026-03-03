# Run เต็มระบบ และ Simple Self-Test

## Simple Self-Test (เทสอย่างเดียว ไม่เปิดเซิร์ฟเวอร์)

ตรวจสอบ DB, โหลดแอป, ทดสอบ API และหน้าหลักด้วย TestClient (ไม่ต้องรัน uvicorn):

```bash
cd code
python scripts/simple_self_test.py
```

- ผ่าน: แสดง `[PASS]` ทุกรายการ และ `Result: N passed, 0 failed` แล้วจบ exit 0
- ไม่ผ่าน: แสดง `[FAIL]` และ exit 1

## Run เต็มระบบ (Migration + Self-Test + เปิดเซิร์ฟเวอร์)

รัน migration สำหรับ member, ทำ self-test แล้วเปิดเซิร์ฟเวอร์ที่พอร์ต 8000:

```bash
cd code
python scripts/run_full_system.py
```

กด Ctrl+C เพื่อหยุดเซิร์ฟเวอร์

### เทสอย่างเดียว (ไม่เปิดเซิร์ฟเวอร์)

```bash
python scripts/run_full_system.py --no-serve
```

จะรัน migration (ถ้าต้องการ) และ simple_self_test เท่านั้น

## รายการที่ Self-Test ตรวจ

1. Database connection
2. App import (main:app)
3. GET /health
4. POST /api/member/register
5. POST /api/member/login
6. GET /api/member/me (Bearer token)
7. GET /api/member/ads
8. GET /api/admin/ecoupon/list
9. GET /member, /member/register, /member/dashboard, /member/scan
10. GET /store-pos-login, /admin
11. GET /store-pos → 302 redirect (ยังไม่ล็อกอิน)

## เปิดเซิร์ฟเวอร์แบบปกติ (ไม่รันเทส)

```bash
cd code
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

จากนั้นเปิดเบราว์เซอร์ที่ http://localhost:8000
