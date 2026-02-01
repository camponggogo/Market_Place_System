# Windows Deployment Guide

## ⚠️ หมายเหตุสำคัญ

**Gunicorn ไม่รองรับ Windows** เพราะใช้ `fcntl` module ที่เป็น Unix-only

## 🪟 ตัวเลือกสำหรับ Windows

### 1. **Uvicorn with Workers** (แนะนำ)

**ข้อดี:**
- ✅ รองรับ Windows
- ✅ เร็วและเสถียร
- ✅ รองรับ async/await
- ✅ ใช้งานง่าย

**วิธีใช้:**
```powershell
# Development
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production (4 workers)
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# หรือใช้ script
.\start_production.ps1
.\start_production_windows.bat
```

**Configuration:**
- Workers: 4 (ปรับตาม CPU)
- Host: 0.0.0.0 (รับ connection จากทุกที่)
- Port: 8000

---

### 2. **Hypercorn** (เร็วกว่า, รองรับ HTTP/2)

**ข้อดี:**
- ✅ รองรับ Windows
- ✅ เร็วที่สุดในบรรดา ASGI servers
- ✅ รองรับ HTTP/2 และ HTTP/3
- ✅ Built-in SSL support

**วิธีใช้:**
```powershell
# ติดตั้ง
pip install hypercorn

# รัน
hypercorn main:app --bind 0.0.0.0:8000 --workers 4

# หรือใช้ config
hypercorn main:app --config hypercorn_config.py
```

---

### 3. **Waitress** (WSGI Server สำหรับ Windows)

**ข้อดี:**
- ✅ รองรับ Windows
- ✅ Production-ready
- ✅ ใช้งานง่าย

**ข้อเสีย:**
- ⚠️ ไม่รองรับ async/await โดยตรง
- ⚠️ ต้องใช้ ASGI-to-WSGI adapter

**วิธีใช้:**
```powershell
# ติดตั้ง
pip install waitress

# รัน (ต้องใช้ ASGI-to-WSGI adapter)
waitress-serve --host=0.0.0.0 --port=8000 --threads=4 main:app
```

---

## 🚀 Production Setup สำหรับ Windows

### Option 1: Uvicorn (แนะนำ)

```powershell
# ติดตั้ง dependencies
pip install uvicorn[standard]

# รัน production
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4 --log-level info
```

### Option 2: Hypercorn

```powershell
# ติดตั้ง
pip install hypercorn

# รัน production
hypercorn main:app --bind 0.0.0.0:8000 --workers 4
```

### Option 3: Windows Service (สำหรับ Production)

ใช้ **NSSM (Non-Sucking Service Manager)** เพื่อรันเป็น Windows Service:

1. ดาวน์โหลด NSSM: https://nssm.cc/download
2. สร้าง service:

```cmd
nssm install FoodCourtService
```

ตั้งค่า:
- **Path**: `C:\Python312\Scripts\uvicorn.exe`
- **Arguments**: `main:app --host 0.0.0.0 --port 8000 --workers 4`
- **Working Directory**: `D:\Projects\FoodCourt`

3. Start service:
```cmd
nssm start FoodCourtService
```

---

## 🔧 Configuration Files

### `start_production.ps1` (PowerShell)
```powershell
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### `start_production_windows.bat` (Batch)
```batch
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 📊 Performance สำหรับ Windows

### สำหรับ Scale: ~1000 users/day, ~200 stores/day

**Uvicorn Configuration:**
- Workers: 4
- Host: 0.0.0.0
- Port: 8000
- Timeout: 60 seconds

**Expected Performance:**
- Response Time: < 200ms
- Concurrent Users: 50-100
- Requests/Second: 10-20

---

## 🔒 Security สำหรับ Public Internet

### 1. Firewall Rules

```powershell
# เปิด port 8000
New-NetFirewallRule -DisplayName "FoodCourt API" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
```

### 2. Reverse Proxy (แนะนำ)

ใช้ **IIS** หรือ **Nginx for Windows** เป็น reverse proxy:

**IIS Configuration:**
- Install URL Rewrite module
- Setup reverse proxy rule
- Enable SSL/TLS

**Nginx for Windows:**
- ดาวน์โหลด: http://nginx.org/en/download.html
- ใช้ config เหมือน `nginx.conf.example`
- Setup SSL certificate

### 3. Rate Limiting

ใช้ middleware ที่สร้างไว้แล้ว (`middleware/security.py`)

---

## 🐛 Troubleshooting

### Error: `ModuleNotFoundError: No module named 'fcntl'`

**สาเหตุ:** Gunicorn ไม่รองรับ Windows

**แก้ไข:** ใช้ Uvicorn หรือ Hypercorn แทน

### Error: `Address already in use`

**แก้ไข:**
```powershell
# หา process ที่ใช้ port 8000
netstat -ano | findstr :8000

# Kill process
taskkill /PID <PID> /F
```

### Error: `Permission denied`

**แก้ไข:** รัน PowerShell as Administrator

---

## 📝 หมายเหตุ

- สำหรับ **Development**: ใช้ `uvicorn main:app --reload`
- สำหรับ **Production**: ใช้ `uvicorn main:app --workers 4`
- สำหรับ **Public Internet**: ควรใช้ reverse proxy (IIS/Nginx) + SSL
- **Gunicorn** ใช้ได้เฉพาะ Linux/Unix/Mac

---

## 🔗 References

- [Uvicorn Documentation](https://www.uvicorn.org/)
- [Hypercorn Documentation](https://hypercorn.readthedocs.io/)
- [NSSM - Windows Service Manager](https://nssm.cc/)
- [IIS URL Rewrite](https://www.iis.net/downloads/microsoft/url-rewrite)

