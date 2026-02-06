# Run/

สคริปต์สำหรับ **รันและตั้งค่า** ระบบ (ต้องรันจาก **root โปรเจกต์**)

## แยกรัน Back-end และ Front-end (Bank API + Webhook)

- **start_backend.ps1** – รัน Back-end เท่านั้น (FastAPI: DB, API, Webhook SCB + K Bank PromptPay)
- **start_frontend.ps1** – เปิดหน้า Customer, Store-POS, Admin, Signage ใน Browser (ต้องรัน Back-end ก่อน)
- **start_all.ps1** – รัน Back-end แล้วเปิด Front-end ในคำสั่งเดียว

ดูโครงสร้างและ flow: **docs/ARCHITECTURE_BANK_AND_RUN.md**

## สคริปต์อื่น

- **quick_start.ps1** / **quick_start.sh** – ติดตั้ง, สร้าง DB, init, สร้าง sample data, เปิด server
- **init_db.py** + **init_db.sql** – สร้าง database และตาราง
- **create_database.py** – สร้าง database
- **create_sample_data.py** – สร้างข้อมูลตัวอย่าง
- **check_setup.py** – ตรวจสอบ dependencies และ config
- **migrate_*.py** – สคริปต์ migration
- **start_production.ps1**, **start_server.py** – รัน server
- **seed_full_sample.ps1**, **seed_scb_store2.ps1**, **seed_kbank_store2.ps1** – seed ข้อมูล + Bank config

## วิธีใช้ (จาก root โปรเจกต์)

```powershell
# Windows – Quick Start
.\Run\quick_start.ps1
```

```bash
# รันสคริปต์ทีละตัว (ต้องตั้ง PYTHONPATH=code ก่อน)
PYTHONPATH=code python Run/create_database.py
PYTHONPATH=code python Run/init_db.py
PYTHONPATH=code python Run/create_sample_data.py
```
