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
   DB_NAME=maket_system
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

## Quick Start Script

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

## หมายเหตุ

- ใช้ virtual environment แนะนำเพื่อหลีกเลี่ยง conflicts
- ตรวจสอบ Python version: `python --version` (ต้อง 3.12+)
- ตรวจสอบ MariaDB version: `mysql --version`

