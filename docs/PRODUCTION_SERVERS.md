# Production Web Servers - ตัวเลือกที่เร็วกว่า FastAPI

## 📊 เปรียบเทียบ Web Servers

| Server | ความเร็ว | HTTP/2 | Production Ready | ความยาก |
|--------|---------|--------|------------------|---------|
| **Uvicorn** (default) | ⭐⭐⭐ | ❌ | ⭐⭐ | ⭐ |
| **Gunicorn + Uvicorn** | ⭐⭐⭐⭐ | ❌ | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| **Hypercorn** | ⭐⭐⭐⭐⭐ | ✅ | ⭐⭐⭐⭐ | ⭐⭐ |
| **Nginx + Uvicorn** | ⭐⭐⭐⭐⭐ | ✅ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

## 🚀 ตัวเลือกที่แนะนำ

### 1. **Gunicorn + Uvicorn Workers** (แนะนำที่สุด)

**ข้อดี:**
- ✅ เร็วและเสถียรสำหรับ production
- ✅ รองรับ multiple workers
- ✅ Process management ที่ดี
- ✅ ใช้งานง่าย

**วิธีใช้:**
```bash
# ติดตั้ง
pip install gunicorn

# รัน
gunicorn main:app -c gunicorn_config.py

# หรือใช้ script
./start_production.sh  # Linux/Mac
.\start_production.ps1  # Windows
```

**Configuration:**
- ไฟล์: `gunicorn_config.py`
- Workers: `(2 x CPU cores) + 1`
- Timeout: 30 seconds

---

### 2. **Hypercorn** (เร็วกว่าที่สุด)

**ข้อดี:**
- ✅ เร็วที่สุดในบรรดา ASGI servers
- ✅ รองรับ HTTP/2 และ HTTP/3
- ✅ Built-in SSL support
- ✅ Async-first design

**ข้อเสีย:**
- ⚠️ ยังใหม่กว่า Gunicorn
- ⚠️ Community น้อยกว่า

**วิธีใช้:**
```bash
# ติดตั้ง
pip install hypercorn

# รัน
hypercorn main:app --config hypercorn_config.py

# หรือ
hypercorn main:app --bind 0.0.0.0:8000 --workers 4
```

**Configuration:**
- ไฟล์: `hypercorn_config.py`
- HTTP/2: Enabled
- Workers: 4 (ปรับตาม CPU)

---

### 3. **Uvicorn with Multiple Workers** (ง่ายที่สุด)

**ข้อดี:**
- ✅ ง่ายที่สุด
- ✅ ไม่ต้องติดตั้งเพิ่ม
- ✅ เร็วพอสำหรับ production เล็ก-กลาง

**ข้อเสีย:**
- ⚠️ ไม่มี process management ที่ดีเท่า Gunicorn
- ⚠️ ไม่รองรับ HTTP/2

**วิธีใช้:**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

### 4. **Nginx + Uvicorn/Gunicorn** (Production แบบเต็มรูปแบบ)

**ข้อดี:**
- ✅ เร็วที่สุดและเสถียรที่สุด
- ✅ รองรับ HTTP/2, SSL/TLS
- ✅ Load balancing
- ✅ Static file serving
- ✅ Reverse proxy

**ข้อเสีย:**
- ⚠️ ต้องติดตั้งและ configure Nginx
- ⚠️ ซับซ้อนกว่า

**วิธีใช้:**

1. ติดตั้ง Nginx:
```bash
# Ubuntu/Debian
sudo apt install nginx

# Windows
# ดาวน์โหลดจาก nginx.org
```

2. Configure Nginx (`/etc/nginx/sites-available/foodcourt`):
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Redirect to HTTPS (ถ้ามี SSL)
    # return 301 https://$server_name$request_uri;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files
    location /static {
        alias /path/to/app/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

3. รัน FastAPI:
```bash
gunicorn main:app -c gunicorn_config.py
```

---

## 📈 Performance Tips

### 1. **Database Connection Pooling**
```python
# ใน app/database.py
engine = create_engine(
    DATABASE_URL,
    pool_size=20,  # เพิ่ม pool size
    max_overflow=40,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

### 2. **Async Database Queries**
ใช้ `async` functions และ `await` อย่างถูกต้อง

### 3. **Caching**
```python
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

# ใช้ Redis สำหรับ caching
```

### 4. **CDN สำหรับ Static Files**
ใช้ CDN (เช่น Cloudflare) สำหรับ static files

---

## 🔧 การเลือกใช้

### สำหรับ Development:
```bash
uvicorn main:app --reload
```

### สำหรับ Production เล็ก-กลาง (< 1000 concurrent users):
```bash
gunicorn main:app -c gunicorn_config.py
# หรือ
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### สำหรับ Production ใหญ่ (> 1000 concurrent users):
```bash
# ใช้ Nginx + Gunicorn
nginx + gunicorn main:app -c gunicorn_config.py
```

### สำหรับความเร็วสูงสุด:
```bash
hypercorn main:app --config hypercorn_config.py
```

---

## 📝 หมายเหตุ

- **FastAPI + Uvicorn** ก็เร็วมากอยู่แล้ว (รองรับ async/await)
- การ optimize code และ database queries สำคัญกว่าการเปลี่ยน server
- สำหรับ public web แนะนำใช้ **Gunicorn + Uvicorn** หรือ **Nginx + Gunicorn**
- **Hypercorn** เหมาะสำหรับ applications ที่ต้องการ HTTP/2

---

## 🔗 References

- [Gunicorn Documentation](https://docs.gunicorn.org/)
- [Hypercorn Documentation](https://hypercorn.readthedocs.io/)
- [Uvicorn Documentation](https://www.uvicorn.org/)
- [Nginx Documentation](https://nginx.org/en/docs/)

