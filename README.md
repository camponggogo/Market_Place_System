# Market_Place_System

**ระบบจัดการตลาดนัด Onlinehelp**

ระบบบริหารจัดการ Food Court / ตลาดนัด ที่รองรับการชำระเงินหลากหลายรูปแบบ พร้อม PromptPay QR Code, จอ Signage แยกสำหรับลูกค้า และการโอนเงินสิ้นวัน (Settlement)

---

## สารบัญ

- [คุณสมบัติหลัก](#คุณสมบัติหลัก)
- [ความต้องการของระบบ](#ความต้องการของระบบ)
- [การติดตั้ง](#การติดตั้ง)
- [การตั้งค่า](#การตั้งค่า)
- [การรัน](#การรัน)
- [Docker](#docker)
- [โครงสร้างโปรเจกต์](#โครงสร้างโปรเจกต์)
- [URLs และหน้าจอ](#urls-และหน้าจอ)
- [เอกสารเพิ่มเติม](#เอกสารเพิ่มเติม)
- [การมีส่วนร่วม](#การมีส่วนร่วม)

---

## คุณสมบัติหลัก

### 1. ระบบ Customer & Balance
- แลกเงินเป็น Food Court ID ที่ Counter (เงินสด / PromptPay / ฯลฯ)
- ตรวจสอบยอดเงินคงเหลือผ่าน QR Code หรือ Web
- ขอคืนเงินที่เหลือ (Refund) ที่ Counter
- Top-up ยอดเพิ่ม

### 2. ระบบร้านค้า (Store POS)
- สร้าง PromptPay QR Code แบบ Tag30 (Bill Payment) และ Tag29 (Credit Transfer)
- Store Token 20 หลัก และ Biller ID สำหรับ QR
- ปุ่มราคาด่วน (Quick Amount) ปรับแก้ได้
- สแกนหรือกรอก Food Court ID เพื่อหักยอด
- จอ Signage แยก (จอที่ 2) แสดง QR และข้อความ "ได้รับเงินเรียบร้อยแล้ว" พร้อม TTS

### 3. Payment Callback & Settlement
- Webhook รับ Back Transaction จากธนาคาร (ref1, ref2, ref3, ยอด, เวลา)
- รายงานการรับเงินและรายการโอนสิ้นวัน (Settlement)
- แจ้งร้านเมื่อโอนเงินแล้ว / สำหรับพิมพ์ใบเสร็จ

### 4. ระบบรายงานและบัญชี
- รายงานยอดขายร้าน (รายวัน/รายเดือน/รายปี)
- Separation of Funds, WHT, VAT
- ใบกำกับภาษี (E-Tax Invoice)

### 5. ระบบอื่นๆ
- จัดการร้านค้า, เมนู, Profile, Event
- ตำแหน่งร้าน (Geo)
- Crypto/E-Contract (ถ้าเปิดใช้)

---

## ความต้องการของระบบ

- **Python** 3.10+
- **MariaDB / MySQL** 5.7+ (หรือ 10.x)
- **pip** สำหรับติดตั้ง dependencies

---

## การติดตั้ง

### 1. Clone โปรเจกต์

```bash
git clone https://github.com/camponggogo/Market_Place_System.git
cd Market_Place_System
```

### 2. สร้าง Virtual Environment (แนะนำ)

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. ติดตั้ง Dependencies

```bash
pip install -r code/requirements.txt
```

### 4. ตั้งค่า Database

- สร้าง Database ชื่อ `maket_place_system` (หรือตามที่กำหนดใน config)
- รันสคริปต์สร้างตารางและข้อมูลเริ่มต้น (จาก root โปรเจกต์):

```bash
# Windows: ตั้ง PYTHONPATH ให้ชี้ไปที่ code/
set PYTHONPATH=code
python Run/create_database.py
python Run/init_db.py
python Run/create_sample_data.py
```

หรือใช้ **Quick Start:** `Run\quick_start.ps1` (Windows) จะทำครบให้

---

## การตั้งค่า

### ไฟล์ config.ini

วางในโฟลเดอร์ **code/** (`code/config.ini`) และแก้ค่าตามสภาพแวดล้อม:

```ini
[DATABASE]
DB_HOST = localhost
DB_PORT = 3306
DB_NAME = maket_place_system
DB_USER = root
DB_PASSWORD = your_password

[BACKEND]
BACKEND_URL = http://localhost:8000
SECRET_KEY = your-secret-key
DEBUG = true

[E_MONEY]
HAS_E_MONEY_LICENSE = false
AUTO_REFUND_ENABLED = true

[PAYMENT]
PROMPTPAY_ENABLED = true
```

### ตัวแปร Environment (Docker / Production)

ถ้าใช้ตัวแปรสภาพแวดล้อม (เช่นใน Docker) ค่าจาก env จะทับค่าจาก `config.ini`  
ดูรายการใน `app/config.py` และ `docker-compose.yml`

---

## การรัน

### โหมดพัฒนา (Development)

จาก **root โปรเจกต์** (ให้ Python เห็นโฟลเดอร์ `code/`):

```bash
# Windows PowerShell
$env:PYTHONPATH="code"; uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Linux / macOS
PYTHONPATH=code uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

หรือใช้สคริปต์ Quick Start (Windows):

```powershell
.\Run\quick_start.ps1
```

### เปิด Swagger / ReDoc (API Docs)

ตั้งค่า environment ก่อนรัน:

```bash
set ENABLE_DOCS=true
uvicorn main:app --reload
```

จากนั้นเปิด:
- **Swagger UI:** http://localhost:8000/docs  
- **ReDoc:** http://localhost:8000/redoc  

### โหมด Production

ใช้ Gunicorn + Uvicorn workers:

```bash
gunicorn main:app --bind 0.0.0.0:8000 --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

---

## Docker

### รันด้วย Docker Compose

จาก **root โปรเจกต์** (มีโฟลเดอร์ `code/`, `Run/`, `Deploy/`):

```bash
docker compose -f Deploy/docker-compose.yml up -d
```

- **App:** http://localhost:8000  
- **DB:** port 3306 (ตาม `DB_PORT` ใน .env)  
- **Nginx:** port 80/443 (ถ้าเปิดใช้)

### ตัวแปรสำคัญใน .env

```env
DB_NAME=maket_place_system
DB_USER=foodcourt_user
DB_PASSWORD=foodcourt_pass
DB_ROOT_PASSWORD=P@ssw0rd@dev
APP_PORT=8000
```

รายละเอียดเพิ่มเติม: [DOCKER_DEPLOY.md](DOCKER_DEPLOY.md)

---

## โครงสร้างโปรเจกต์

```
Market_Place_System/
├── README.md             # คู่มือหลัก (ที่คุณกำลังอ่าน)
├── docs/                 # เอกสาร (API, User Manual, Deployment)
│
├── code/                 # โค้ดแอปทั้งหมด
│   ├── app/              # API, models, services, static, contracts, utils
│   ├── main.py           # FastAPI entry
│   ├── config.ini        # Config (override ได้ด้วย env)
│   ├── requirements.txt
│   ├── middleware/
│   ├── tests/
│   └── hardware/
│
├── Run/                  # สคริปต์รัน / ตั้งค่า
│   ├── quick_start.ps1   # Quick Start (Windows)
│   ├── quick_start.sh
│   ├── init_db.py        # สร้าง DB + ตารางจาก init_db.sql
│   ├── init_db.sql
│   ├── create_database.py
│   ├── create_sample_data.py
│   ├── check_setup.py
│   └── ...
│
└── Deploy/               # Docker และ Deploy
    ├── Dockerfile
    ├── docker-compose.yml
    ├── nginx/
    ├── deploy.sh, deploy_remote.ps1, ...
    └── DOCKER_DEPLOY.md
```

---

## URLs และหน้าจอ

| หน้าที่ | URL | คำอธิบาย |
|--------|-----|----------|
| หน้าแรก (Redirect) | `/` | ไปที่ `/admin` |
| Admin Dashboard | `/admin` | แดชบอร์ดจัดการระบบ |
| Store POS | `/store-pos?store_id=1` | หน้าจอ POS ร้าน (ใส่เงิน, สร้าง QR, หักยอด) |
| Launch (2 จอ) | `/launch?store_id=1` | เปิด Store POS + Signage ใน 2 หน้าต่าง |
| Signage | `/signage` | จอที่ 2 แสดง QR / ข้อความได้รับเงิน |
| Customer | `/customer` | หน้าลูกค้า (ตรวจสอบยอด ฯลฯ) |
| Customer QR | `/customer-qr` | หน้าสแกน QR ตรวจสอบยอด |
| Health Check | `/health` | ตรวจสอบสถานะ API |

---

## เอกสารเพิ่มเติม

- **[API Documentation](docs/API_DOCUMENTATION.md)** – รายละเอียด API ทุก endpoint สำหรับ Developer  
- **[User Manual](docs/USER_MANUAL.md)** – คู่มือการใช้งานสำหรับผู้ใช้ (Admin, ร้านค้า, Counter, ลูกค้า)  
- [DOCKER_DEPLOY.md](DOCKER_DEPLOY.md) – การ Deploy ด้วย Docker  
- [QUICK_START.md](QUICK_START.md) – เริ่มต้นใช้งานอย่างรวดเร็ว  

---

## การมีส่วนร่วม

1. Fork โปรเจกต์  
2. สร้าง branch สำหรับ feature (`git checkout -b feature/xxx`)  
3. Commit การเปลี่ยนแปลง (`git commit -m 'Add feature xxx'`)  
4. Push ไปที่ branch (`git push origin feature/xxx`)  
5. เปิด Pull Request  

---

## License

โปรเจกต์นี้พัฒนาเพื่อระบบจัดการตลาดนัด Onlinehelp
