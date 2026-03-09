# พัฒนาบน Cloud ผ่าน SSH + รันใน Docker พอร์ต 639

โปรเจกต์ตั้งค่าให้แอปรันใน Docker **บนพอร์ต 639 เสมอ** เพื่อใช้ร่วมกับ reverse proxy (Nginx ฯลฯ) ที่ออก HTTPS ให้ — ไม่ต้องพึ่ง ngrok ที่ย้าย URL ทุกครั้ง และใช้ **HTTPS จริง** ได้เลย

## โครงแบบที่แนะนำ

1. **Deploy โปรเจกต์ขึ้น Cloud** (VPS / VM ที่มี public IP หรือโดเมน)
2. **แก้ไขโค้ดผ่าน SSH** — clone repo บน server แล้วแก้ไฟล์ผ่าน `vim`/`nano` หรือ mount โฟลเดอร์จากเครื่องคุณ (rsync / IDE Remote-SSH)
3. **รันแอปใน Docker** — แอป listen ที่ **port 639** (ใน container และ map ออก host)
4. **HTTPS ด้านหน้า** — ใช้ Nginx (หรือ Caddy / Cloudflare Tunnel) รับ 80/443 แล้ว proxy ไปที่ `app:639` (หรือ `localhost:639` ถ้าไม่ใช้ Docker network)

ผลลัพธ์:
- **URL ไม่ย้าย** — ใช้โดเมนหรือ IP ของ server เดิม
- **Stripe Webhook** — ลงทะเบียน `https://your-domain.com/api/payment-callback/webhook/stripe` ใน Dashboard ได้เลย ไม่ต้องเปลี่ยนตาม ngrok

---

## พอร์ต 639

- **ใน Docker:** แอป (Gunicorn) bind ที่ `0.0.0.0:639` ใน container
- **docker-compose:** map `${APP_PORT:-639}:639` — ถ้าไม่กำหนด `APP_PORT` จะใช้ 639 ที่ host
- **Nginx:** proxy ไปที่ `app:639` (service name ใน docker-compose)

ถ้าต้องการให้ host ใช้พอร์ตอื่น (เช่น 80 อยู่แล้ว) ตั้งใน `.env`:
```bash
APP_PORT=639
```

---

## ขั้นตอนบน Cloud (สรุป)

### 1. เตรียม server
- ติดตั้ง Docker + Docker Compose
- (ถ้าใช้ HTTPS) เตรียมโดเมนชี้มาที่ server หรือใช้ IP

### 2. Clone / อัปโค้ด
```bash
git clone <repo-url> FoodCourt
cd FoodCourt
```

### 3. ตั้งค่า environment
สร้าง `Deploy/.env` (หรือ export ตัวแปร):
```bash
# ใช้ HTTPS จริง — ใส่ URL ที่ user เข้าถึง (หลัง Nginx/SSL)
BACKEND_URL=https://your-domain.com

# หรือถ้าเข้า via IP และยังไม่มี SSL
# BACKEND_URL=http://YOUR_SERVER_IP

# Database (ตรงกับใน docker-compose)
DB_NAME=market_place_system
DB_USER=marketplace_user
DB_PASSWORD=your_db_password
```

### 4. Build และรัน
```bash
cd Deploy
docker compose up -d --build
```

แอปจะรันใน container และ listen ที่ **port 639**; Nginx (ถ้าเปิดใช้) จะรับ 80/443 แล้ว proxy ไปที่แอป

### 5. พัฒนา / แก้โค้ดผ่าน SSH
- แก้ไฟล์ใน `code/` บน server (vim, nano, หรือ Remote-SSH จาก IDE)
- ถ้าใช้ volume mount โปรเจกต์ (`../code` ใน docker-compose) การแก้ไฟล์ใน `code/` บางส่วนจะ reflect ทันที (static files); ถ้าแก้ Python ต้อง **rebuild หรือ restart container**:
  ```bash
  docker compose up -d --build app
  ```

### 6. Stripe Webhook (เมื่อใช้ HTTPS จริง)
- ลงทะเบียนใน Stripe Dashboard: **Endpoint URL** = `https://your-domain.com/api/payment-callback/webhook/stripe`
- Copy **Signing secret** (whsec_...) → ใส่ใน `code/config.ini` ที่ `STRIPE_WEBHOOK_SECRET`
- ตั้ง `STRIPE_WEBHOOK_CHANNEL=ngrok` หรือ `custom`; ถ้าใช้โดเมนจริง ตั้ง `custom` และ `STRIPE_WEBHOOK_URL=https://your-domain.com/api/payment-callback/webhook/stripe`

---

## ไม่มี SSL ที่ server เอง

ถ้า server ไม่มี certificate (ไม่มี HTTPS ที่ตัว server):
- ใช้ **Cloudflare Tunnel** (cloudflared) หรือ reverse proxy ภายนอกที่ออก HTTPS ให้ แล้ว proxy มาที่ `http://localhost:639` หรือ `http://app:639`
- ตั้ง `BACKEND_URL` และ Stripe Webhook URL เป็น **HTTPS URL** ที่ tunnel หรือ proxy ให้มา

---

## อ้างอิง

- Docker: `Deploy/docker-compose.yml`, `Deploy/Dockerfile`
- Nginx upstream: `Deploy/nginx/nginx.conf` → `app:639`
- Stripe: `code/docs/STRIPE_NGROK.md`, `code/docs/STRIPE_CLI_VS_API.md`
