# คู่มือเริ่มต้นใช้งานระบบ Food Court Management System

## ✅ สถานะการตั้งค่า

- ✅ Database: **MariaDB**
- ✅ User: **root**
- ✅ Password: **123456**
- ✅ Port: **3306**
- ✅ Database Name: **foodcourt**

## 📋 ขั้นตอนการติดตั้งและเริ่มใช้งาน

### 1. ติดตั้ง Dependencies

```bash
pip install -r requirements.txt
```

หรือถ้ามี conflicts:
```bash
pip install PyMySQL cryptography
pip install fastapi uvicorn sqlalchemy pydantic python-dotenv
```

### 2. สร้าง Database ใน MariaDB

เชื่อมต่อ MariaDB และรันคำสั่ง:

```sql
CREATE DATABASE foodcourt CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

หรือใช้ command line:
```bash
mysql -u root -p123456 -e "CREATE DATABASE foodcourt CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

### 3. สร้าง Database Tables และข้อมูลตัวอย่าง

```bash
python scripts/init_db.py
```

หรือ:
```bash
python -m scripts.init_db
```

### 4. ตรวจสอบการตั้งค่า

ตรวจสอบไฟล์ `config.ini` ว่าตั้งค่าถูกต้อง:

```ini
[DATABASE]
DB_HOST=localhost
DB_PORT=3306
DB_NAME=foodcourt
DB_USER=root
DB_PASSWORD=123456
```

### 5. รันระบบ

```bash
uvicorn main:app --reload
```

ระบบจะรันที่: **http://localhost:8000**

### 6. ตรวจสอบระบบ

- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health
- Customer Interface: http://localhost:8000/static/index.html
- Store Dashboard: http://localhost:8000/static/store_dashboard.html

## 🔧 การแก้ปัญหา

### ปัญหา: ModuleNotFoundError

```bash
# ตรวจสอบว่า install dependencies แล้ว
pip list | grep PyMySQL

# ถ้ายังไม่มี ให้ติดตั้ง
pip install PyMySQL cryptography
```

### ปัญหา: Database Connection Error

1. ตรวจสอบว่า MariaDB service ทำงานอยู่:
   ```bash
   # Windows
   net start mariadb
   
   # Linux
   sudo systemctl status mariadb
   ```

2. ตรวจสอบว่า database สร้างแล้ว:
   ```bash
   mysql -u root -p123456 -e "SHOW DATABASES;"
   ```

3. ตรวจสอบสิทธิ์ user:
   ```sql
   GRANT ALL PRIVILEGES ON foodcourt.* TO 'root'@'localhost';
   FLUSH PRIVILEGES;
   ```

### ปัญหา: Port 3306 ถูกใช้งาน

แก้ไข `config.ini`:
```ini
DB_PORT=3307  # หรือ port อื่นที่ว่าง
```

## 📝 ข้อมูลตัวอย่าง

หลังจากรัน `init_db.py` จะมีข้อมูลตัวอย่าง:

- **Store ID**: 1 (ร้านอาหารตัวอย่าง)
- **Customer ID**: 1 (ลูกค้าตัวอย่าง)
- **Customer Phone**: 0812345678
- **Balance**: 100.00 บาท

## 🚀 ขั้นตอนถัดไป

1. ตั้งค่า LINE OA (ถ้าต้องการใช้ Push Notification)
2. ตั้งค่า PromptPay API (ถ้าต้องการใช้ PromptPay Refund)
3. ตั้งค่า Blockchain Explorer API (ถ้าต้องการใช้ Crypto Payment)
4. ตั้งค่า E-Tax Invoice Provider (ถ้าต้องการส่งใบกำกับภาษีอัตโนมัติ)

## 📚 เอกสารเพิ่มเติม

- `DEPLOYMENT.md` - คู่มือการติดตั้งและใช้งานแบบละเอียด
- `FEATURES.md` - รายละเอียดคุณสมบัติระบบ
- `SETUP.md` - คู่มือการแก้ปัญหา Dependencies

