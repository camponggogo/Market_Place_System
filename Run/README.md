# Run/

สคริปต์สำหรับ **รันและตั้งค่า** ระบบ (ต้องรันจาก **root โปรเจกต์**)

- **quick_start.ps1** / **quick_start.sh** – ติดตั้ง, สร้าง DB, init, สร้าง sample data, เปิด server
- **init_db.py** + **init_db.sql** – สร้าง database และตาราง
- **create_database.py** – สร้าง database
- **create_sample_data.py** – สร้างข้อมูลตัวอย่าง
- **check_setup.py** – ตรวจสอบ dependencies และ config
- **migrate_*.py** – สคริปต์ migration
- **start_production.ps1**, **start_server.py** – รัน server

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
