# 🚀 Server Startup Guide

## ⚠️ สำคัญ: Gunicorn ไม่รองรับ Windows

**Gunicorn ใช้ `fcntl` module ที่เป็น Unix-only** ดังนั้นไม่สามารถรันบน Windows ได้

---

## 🪟 สำหรับ Windows

### วิธีที่ 1: ใช้ Script อัตโนมัติ (แนะนำ)

```powershell
python start_server.py
```

Script จะตรวจสอบ OS และแนะนำตัวเลือกที่เหมาะสม

### วิธีที่ 2: ใช้ Uvicorn โดยตรง

```powershell
# Development
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production (4 workers)
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### วิธีที่ 3: ใช้ Hypercorn

```powershell
# ติดตั้ง
pip install hypercorn

# รัน
hypercorn main:app --bind 0.0.0.0:8000 --workers 4
```

### วิธีที่ 4: ใช้ PowerShell Script

```powershell
.\start_production.ps1
```

### วิธีที่ 5: ใช้ Batch File

```cmd
start_production_windows.bat
```

---

## 🐧 สำหรับ Linux/Unix/Mac

### วิธีที่ 1: ใช้ Gunicorn (แนะนำสำหรับ production)

```bash
# ติดตั้ง
pip install gunicorn

# รัน
gunicorn main:app -c gunicorn_config.py

# หรือใช้ script
./start_production.sh
```

### วิธีที่ 2: ใช้ Uvicorn

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### วิธีที่ 3: ใช้ Hypercorn

```bash
hypercorn main:app --config hypercorn_config.py
```

---

## 📊 เปรียบเทียบ

| Server | Windows | Linux/Unix | ความเร็ว | HTTP/2 | Production |
|--------|---------|------------|---------|--------|------------|
| **Gunicorn** | ❌ | ✅ | ⭐⭐⭐⭐ | ❌ | ⭐⭐⭐⭐⭐ |
| **Uvicorn** | ✅ | ✅ | ⭐⭐⭐⭐ | ❌ | ⭐⭐⭐⭐ |
| **Hypercorn** | ✅ | ✅ | ⭐⭐⭐⭐⭐ | ✅ | ⭐⭐⭐⭐ |

---

## 🔧 Quick Start

### Windows:
```powershell
python start_server.py
# หรือ
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Linux/Unix/Mac:
```bash
python start_server.py
# หรือ
gunicorn main:app -c gunicorn_config.py
```

---

## 📝 หมายเหตุ

- **Development**: ใช้ `uvicorn main:app --reload`
- **Production Windows**: ใช้ `uvicorn main:app --workers 4`
- **Production Linux/Unix**: ใช้ `gunicorn main:app -c gunicorn_config.py`
- **ต้องการ HTTP/2**: ใช้ `hypercorn`

---

## 🐛 Troubleshooting

### Error: `ModuleNotFoundError: No module named 'fcntl'`

**สาเหตุ:** พยายามใช้ Gunicorn บน Windows

**แก้ไข:** ใช้ Uvicorn หรือ Hypercorn แทน

```powershell
# แทนที่จะใช้
gunicorn main:app -c gunicorn_config.py  # ❌ ไม่ทำงานบน Windows

# ใช้
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4  # ✅
```

---

## 📚 เอกสารเพิ่มเติม

- `docs/WINDOWS_DEPLOYMENT.md` - คู่มือ Windows deployment
- `docs/PRODUCTION_SERVERS.md` - เปรียบเทียบ production servers
- `docs/DEPLOYMENT_PRODUCTION.md` - คู่มือ production deployment

