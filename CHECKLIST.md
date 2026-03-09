# ✅ Checklist การตั้งค่าระบบ Food Court Management System

## 📦 การติดตั้ง Dependencies

- [ ] ติดตั้ง Python packages: `pip install -r requirements.txt`
- [ ] ตรวจสอบว่า PyMySQL ติดตั้งแล้ว: `pip list | grep PyMySQL`
- [ ] ตรวจสอบว่า cryptography ติดตั้งแล้ว: `pip list | grep cryptography`

## 🗄️ การตั้งค่า Database

- [ ] MariaDB service ทำงานอยู่
- [ ] สร้าง database `market_place_system` แล้ว
- [ ] ตรวจสอบ connection: `mysql -u root -p123456 -e "USE market_place_system;"`
- [ ] ตรวจสอบไฟล์ `config.ini` ตั้งค่าถูกต้อง

## 🏗️ การสร้าง Database Schema

- [ ] รัน `python scripts/init_db.py` สำเร็จ
- [ ] ตรวจสอบว่า tables สร้างแล้ว: `SHOW TABLES;`
- [ ] ตรวจสอบว่ามีข้อมูลตัวอย่าง (Store, Customer)

## 🚀 การรันระบบ

- [ ] รัน `uvicorn main:app --reload` สำเร็จ
- [ ] เข้าถึง API docs ได้: http://localhost:8000/docs
- [ ] Health check ผ่าน: http://localhost:8000/health
- [ ] Customer Interface ทำงาน: http://localhost:8000/static/index.html

## 🔧 การตั้งค่าเพิ่มเติม (Optional)

- [ ] ตั้งค่า LINE OA Channel (ถ้าต้องการ)
- [ ] ตั้งค่า PromptPay API (ถ้าต้องการ)
- [ ] ตั้งค่า Blockchain Explorer API (ถ้าต้องการ)
- [ ] ตั้งค่า E-Tax Invoice Provider (ถ้าต้องการ)

## ✅ การทดสอบระบบ

- [ ] ทดสอบ API: `GET /health`
- [ ] ทดสอบ Customer Balance Check
- [ ] ทดสอบ Refund Request
- [ ] ทดสอบ Crypto Contract (ถ้าเปิดใช้งาน)
- [ ] ทดสอบ Tax Invoice Generation

## 📝 หมายเหตุ

- ตรวจสอบ logs ถ้ามี error
- ตรวจสอบ database connection ถ้ามีปัญหา
- ตรวจสอบ port 8000 ว่าว่าง (หรือเปลี่ยน port ใน uvicorn)

