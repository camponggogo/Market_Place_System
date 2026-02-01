# คู่มือการติดตั้งระบบ Food Court Management System

## ⚠️ หมายเหตุสำคัญเกี่ยวกับ Dependencies

โปรเจคนี้มี dependencies ที่อาจ conflict กับ packages อื่นๆ ที่ติดตั้งอยู่ในระบบของคุณ (เช่น deepface, inference, mediapipe, ortools, roboflow)

**แนะนำให้ใช้ Virtual Environment แยกสำหรับโปรเจคนี้**

## วิธีที่ 1: ใช้ Virtual Environment (แนะนำ)

### สร้าง Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

### ติดตั้ง Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## วิธีที่ 2: ติดตั้งแบบ Minimal (ถ้ามี conflicts)

ถ้ายังมี conflicts อยู่ ให้ใช้ไฟล์ `requirements-minimal.txt` แทน:

```bash
pip install -r requirements-minimal.txt
```

## วิธีที่ 3: ติดตั้งแบบไม่ตรวจสอบ Dependencies (ไม่แนะนำ)

```bash
pip install --no-deps -r requirements.txt
```

**⚠️ วิธีนี้อาจทำให้ระบบไม่ทำงานได้อย่างถูกต้อง**

## การแก้ปัญหา Dependencies Conflicts

### ถ้ามี packages อื่นๆ ติดตั้งอยู่แล้ว

1. **ใช้ Virtual Environment** (แนะนำที่สุด)
2. **อัพเดท packages ที่มีอยู่:**
   ```bash
   pip install --upgrade aiohttp httpx numpy pandas pydantic pillow requests
   ```
3. **ติดตั้งเฉพาะ packages ที่จำเป็น:**
   ```bash
   pip install fastapi uvicorn sqlalchemy psycopg2-binary
   ```

### Packages ที่อาจต้องอัพเดท

- `aiohttp`: ต้อง >= 3.10.9 (สำหรับ line-bot-sdk)
- `httpx`: ต้อง >= 0.28.1 (สำหรับ inference packages)
- `numpy`: ต้อง >= 2.0.0, < 2.3.0 (สำหรับ inference packages)
- `pandas`: ต้อง >= 2.2.3, < 3.0.0 (สำหรับ inference packages)
- `pydantic`: ต้อง >= 2.8.0, < 2.12.0 (สำหรับ inference packages)
- `pillow`: ต้อง >= 11.0, < 12.0 (สำหรับ inference packages)

## ตรวจสอบการติดตั้ง

```bash
python -c "import fastapi; import sqlalchemy; import pydantic; print('All core packages installed successfully!')"
```

## เริ่มใช้งาน

```bash
# สร้าง Database Tables
# วิธีที่ 1: รันจาก root directory
python scripts/init_db.py

# วิธีที่ 2: ใช้ Python module syntax (แนะนำ)
python -m scripts.init_db

# รันระบบ
uvicorn main:app --reload
```

**หมายเหตุ**: Script `init_db.py` จะเพิ่ม root directory เข้า Python path อัตโนมัติ ดังนั้นสามารถรันได้จากที่ไหนก็ได้

## หมายเหตุ

- ถ้าคุณใช้ packages อื่นๆ (deepface, inference, mediapipe) ในโปรเจคอื่น ควรแยก virtual environment
- Food Court System ไม่ต้องการ packages เหล่านั้น ดังนั้นไม่ควรมี conflicts ถ้าใช้ virtual environment แยก

