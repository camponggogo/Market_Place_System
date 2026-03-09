# คู่มือการติดตั้งและตรวจสอบระบบ

## ขั้นตอนการติดตั้ง

### 1. ติดตั้ง Dependencies

```bash
# วิธีที่ 1: ใช้ script (แนะนำ)
python scripts/install_dependencies.py

# วิธีที่ 2: ติดตั้งด้วยมือ
pip install -r requirements.txt

# วิธีที่ 3: ติดตั้งพร้อม test dependencies
pip install -r requirements.txt -r requirements-test.txt
```

### 2. ตรวจสอบการตั้งค่า

```bash
python scripts/check_setup.py
```

Script นี้จะตรวจสอบ:
- ✅ Dependencies ที่ติดตั้งแล้ว
- ✅ ไฟล์ config.ini
- ✅ ไฟล์สำคัญทั้งหมด
- ✅ API modules
- ✅ การเชื่อมต่อ database

### 3. สร้าง Database

```bash
# สร้าง database
python scripts/create_database.py

# สร้าง tables และข้อมูลตัวอย่าง
python scripts/init_db.py
```

### 4. รันระบบ

```bash
uvicorn main:app --reload
```

## การแก้ปัญหา

### ปัญหา: Dependencies ไม่ครบ

```bash
# รัน script ตรวจสอบ
python scripts/check_setup.py

# ติดตั้ง dependencies ที่ขาด
python scripts/install_dependencies.py
```

### ปัญหา: Database Connection Error

1. ตรวจสอบว่า MariaDB ทำงานอยู่:
   ```bash
   # Windows
   net start mariadb
   
   # Linux
   sudo systemctl status mariadb
   ```

2. ตรวจสอบ config.ini:
   ```ini
   [DATABASE]
   DB_HOST=localhost
   DB_PORT=3306
   DB_NAME=market_system
   DB_USER=root
   DB_PASSWORD=123456
   ```

3. สร้าง database:
   ```bash
   python scripts/create_database.py
   ```

### ปัญหา: Import Errors

```bash
# ตรวจสอบว่าไฟล์ครบหรือไม่
python scripts/check_setup.py

# ถ้ามี module ที่ขาด ให้ติดตั้งใหม่
pip install -r requirements.txt --force-reinstall
```

### ปัญหา: ข้อมูล store / เมนู / user สำหรับ Store POS หาย

รันสคริปต์ seed เพื่อสร้างร้านค้า เมนู ราคาด่วน และผู้ใช้ล็อกอิน Store POS ใหม่:

```powershell
# จากโฟลเดอร์โปรเจกต์ (ที่เดียวกับ Run)
$env:PYTHONPATH = "d:\Projects\FoodCourt\code"
python Run/seed_stores_menus_users.py
```

จะได้ร้าน 5 ร้าน (ร้านอาหารไทย, ก๋วยเตี๋ยว, ข้าวผัด, เครื่องดื่ม, ของหวาน) พร้อมเมนูและราคาด่วน ผู้ใช้ `pos1`–`pos5` (รหัสผ่าน `pos123`) ผูกกับ store 1–5 และ admin (`admin` / `admin123`)

**สมาชิกตัวอย่าง (Member)** — ใช้ทดสอบหน้า `/member` ลงทะเบียน/ล็อกอิน:

1. ถ้า DB ยังไม่มีคอลัมน์ `username`, `email`, `password_hash` ในตาราง `customers` ให้รัน migration ก่อน (ครั้งเดียว):
   - **แนะนำ (ไม่ต้องมีโปรแกรม mysql):** `python Run/run_migrations.py` — ใช้การเชื่อมต่อจาก config.ini
   - หรือใช้ mysql โดยตรง: CMD/Bash `mysql -u root -p market_place_system < Run/migrate_customers_member.sql` / PowerShell `.\Run\run_migrate_customers_member.ps1`
2. รัน seed สมาชิก:
   ```powershell
   $env:PYTHONPATH = "d:\Projects\FoodCourt\code"
   python Run/seed_members.py
   ```

จะได้สมาชิก `member1` (รหัส `member123`), `member2`, `demo` (รหัส `demo1234`), `testuser` (รหัส `test1234`) — ใช้ชื่อผู้ใช้หรือเบอร์โทร + รหัสผ่านเข้าสู่ระบบที่ `/member` ได้

### ปัญหา: ngrok แสดง ERR_NGROK_3200 / Endpoint is offline

ข้อความนี้หมายความว่า **backend (Uvicorn) ที่พอร์ต 8000 ยังไม่รันหรือไม่ตอบ** — ngrok ทำงานแล้ว แต่ไม่มีแอปให้ forward ไป

**ทำตามลำดับนี้:**

1. **รัน backend ก่อน (พอร์ต 8000)**  
   จากโฟลเดอร์โปรเจกต์ (ที่เดียวกับ `Run`):
   ```powershell
   $env:PYTHONPATH = "d:\Projects\FoodCourt\code"
   cd d:\Projects\FoodCourt\code
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```
   หรือใช้ `Run\quick_start.ps1` (จะเปิดทั้ง ngrok และ server ให้)

2. **ตรวจว่า local ใช้ได้**  
   เปิดเบราว์เซอร์ไปที่ `http://localhost:8000/store-pos-login`  
   ถ้าเข้าได้ แสดงว่า backend พร้อม

3. **จากนั้นค่อยเปิด URL ของ ngrok**  
   ใช้ลิงก์ที่ ngrok แสดง (เช่น `https://xxxx.ngrok-free.app/store-pos-login?next=/store-pos`)

**ถ้าใช้ quick_start.ps1:** สคริปต์จะเปิด 2 หน้าต่าง — อย่าปิดหน้าต่างที่รัน Uvicorn ถ้าต้องการให้ ngrok ยังใช้ได้

### ปัญหา: Stripe ส่ง webhook ไม่ได้ (403 Forbidden ที่ Dashboard)

เมื่อใช้ **ngrok แบบฟรี** เป็น URL สำหรับ Stripe Webhook แล้ว Stripe Dashboard แสดง **403 ERR Forbidden** — สาเหตุคือ ngrok จะบล็อก request ที่ไม่ใช่เบราว์เซอร์ (เช่น request จากเซิร์ฟเวอร์ Stripe) จึงไม่ส่ง request ไปถึง API ของเรา

**ทางเลือกแก้ไข:**

1. **ใช้ ngrok แผนจ่าย (แนะนำถ้าต้องการ webhook จริง)**  
   - ใน [ngrok Dashboard](https://dashboard.ngrok.com) สร้าง Edge แล้วเพิ่ม Request Header: `ngrok-skip-browser-warning: true`  
   - หรือรันด้วย config: `request_header.add: ["ngrok-skip-browser-warning: true"]`  
   - จากนั้นใช้ URL จาก tunnel นั้นเป็น Webhook URL ใน Stripe

2. **ใช้ tunnel อื่นที่ไม่บล็อก server request**  
   - เช่น [cloudflared](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps) (`cloudflared tunnel --url http://localhost:8000`)  
   - ใส่ URL ที่ได้เป็น Webhook endpoint ใน Stripe Dashboard

3. **ทดสอบบน production / server ที่มี domain จริง**  
   - ลงทะเบียน Webhook ใน Stripe เป็น `https://yourdomain.com/api/payment-callback/webhook/stripe`  
   - ไม่ผ่าน ngrok จึงไม่มี 403 จาก browser warning

4. **ระบบใช้ Stripe API เป็นหลัก** — ลงทะเบียน Webhook URL (จาก ngrok หรือโดเมน) ใน Stripe Dashboard แล้วใส่ Signing secret ใน config; ถ้าต้องการทดสอบแบบไม่ใช้ URL สาธารณะ ตั้ง `STRIPE_WEBHOOK_CHANNEL=stripe_cli` แล้วรัน `stripe listen --forward-to localhost:8000/api/payment-callback/webhook/stripe`

**หมายเหตุ:** เราได้ยกเว้น path `/api/payment-callback/webhook` จาก rate limit แล้ว เพื่อไม่ให้ middleware บล็อก request จาก Stripe

### ปัญหา: ngrok แสดง ERR_NGROK_727 / HTTP Requests exceeded

บัญชี **ngrok แบบฟรีมีโควต้า HTTP จำกัด** เมื่อเกินแล้วจะเปิดลิงก์ `https://xxx.ngrok-free.app` ไม่ได้

**ทางเลือก (ไม่ต้องอัปเกรด):**

- **ใช้ localhost แทน** — เปิดแอปในเครื่องตัวเองได้ปกติ ไม่กินโควต้า ngrok  
  เปิดเบราว์เซอร์ไปที่:
  ```
  http://localhost:8000/launch?store_id=1
  ```
  หรือหน้าเข้าสู่ระบบ Store POS:
  ```
  http://localhost:8000/store-pos-login?next=/store-pos
  ```
- ตรวจว่า **Uvicorn รันอยู่ที่พอร์ต 8000** (หน้าต่างที่รัน `uvicorn main:app --reload --host 0.0.0.0 --port 8000` ยังไม่ปิด)
- ใช้ ngrok เฉพาะตอนที่ต้อง**แชร์ลิงก์ให้คนอื่นจากภายนอก** และรอโควต้า reset (หรืออัปเกรดแผนจ่าย)

## Quick Start Script

**Windows:** ใช้ `Run\quick_start.ps1` ได้เลย — สคริปต์จะติดตั้ง Python dependencies, (ถ้ามี Scoop) **Stripe CLI** สำหรับรับ webhook ทดสอบ, ตรวจสอบ setup, สร้าง DB, seed ข้อมูล แล้วเปิด server และ ngrok ถ้ามี

สร้างไฟล์ `quick_start.bat` (Windows) หรือ `quick_start.sh` (Linux/Mac):

### Windows (quick_start.bat)
```batch
@echo off
echo Installing dependencies...
python scripts/install_dependencies.py

echo.
echo Checking setup...
python scripts/check_setup.py

echo.
echo Creating database...
python scripts/create_database.py

echo.
echo Initializing database...
python scripts/init_db.py

echo.
echo Starting server...
uvicorn main:app --reload
```

### Linux/Mac (quick_start.sh)
```bash
#!/bin/bash
echo "Installing dependencies..."
python scripts/install_dependencies.py

echo ""
echo "Checking setup..."
python scripts/check_setup.py

echo ""
echo "Creating database..."
python scripts/create_database.py

echo ""
echo "Initializing database..."
python scripts/init_db.py

echo ""
echo "Starting server..."
uvicorn main:app --reload
```

## Checklist

- [ ] Python 3.12+ ติดตั้งแล้ว
- [ ] MariaDB ติดตั้งและทำงานอยู่
- [ ] Dependencies ติดตั้งแล้ว (`pip install -r requirements.txt`)
- [ ] config.ini ตั้งค่าถูกต้อง
- [ ] Database สร้างแล้ว (`python scripts/create_database.py`)
- [ ] Tables สร้างแล้ว (`python scripts/init_db.py`)
- [ ] ระบบรันได้ (`uvicorn main:app --reload`)

## การตั้งค่า Stripe (เติมเงินสมาชิก / PromptPay)

ถ้าหน้าเติมเงินสมาชิกหรือ Store POS แสดง "Stripe ยังไม่ได้ตั้งค่า" ให้ตั้งค่า API Key ดังนี้:

1. **ดึงคีย์จาก Stripe:** ไปที่ [Stripe Dashboard → API Keys](https://dashboard.stripe.com/apikeys)  
   - **Publishable key** (pk_test_... หรือ pk_live_...)  
   - **Secret key** (sk_test_... หรือ sk_live_...)

2. **วิธีที่ 1 – แก้ใน config.ini (รันแบบ local):**  
   เปิด `code/config.ini` หา section `[STRIPE]` แล้วใส่ค่าจริง:
   ```ini
   [STRIPE]
   STRIPE_SECRET_KEY=sk_test_xxxxxxxx
   STRIPE_PUBLISHABLE_KEY=pk_test_xxxxxxxx
   ```

3. **วิธีที่ 2 – ใช้ตัวแปรสภาพแวดล้อม (Docker หรือ production):**  
   ตั้งใน `.env` หรือ environment:
   ```bash
   STRIPE_SECRET_KEY=sk_test_xxxxxxxx
   STRIPE_PUBLISHABLE_KEY=pk_test_xxxxxxxx
   ```
   ถ้ารัน Docker จากโฟลเดอร์ Deploy ให้สร้างไฟล์ `.env`  рядомกับ `docker-compose.yml` แล้วใส่สองบรรทัดด้านบน จากนั้นรัน `docker-compose up -d` ใหม่

หลังตั้งค่าแล้ว รีสตาร์ทแอป (หรือ container) แล้วลองกดเติมเงินอีกครั้ง

**Stripe Webhook (จ่าย PromptPay แล้วให้ระบบอัปเดต):** ระบบใช้ **Stripe API** (ลงทะเบียน URL ใน Dashboard) เป็นหลัก — ใช้ ngrok หรือโดเมนที่ได้ HTTPS; ดูขั้นตอนใน `code/docs/STRIPE_NGROK.md` และแนวทาง deploy บน Cloud Docker ใน `code/docs/STRIPE_CLI_VS_API.md`

## หมายเหตุ

- ใช้ virtual environment แนะนำเพื่อหลีกเลี่ยง conflicts
- ตรวจสอบ Python version: `python --version` (ต้อง 3.12+)
- ตรวจสอบ MariaDB version: `mysql --version`

