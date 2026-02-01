# 🚀 Quick Deploy Guide - Docker

## Deploy บน Server: 150.95.85.185

### วิธีที่ 1: Deploy โดยตรงบน Server (แนะนำ)

```bash
# 1. เชื่อมต่อ server
ssh root@150.95.85.185
# Password: P@ssw0rd@dev

# 2. อัปโหลด project (เลือกวิธีใดวิธีหนึ่ง)

# วิธี A: ใช้ Git
cd /opt
git clone <your-repo> foodcourt
cd foodcourt

# วิธี B: ใช้ SCP จากเครื่อง local
# บนเครื่อง local (PowerShell):
scp -r D:\Projects\FoodCourt root@150.95.85.185:/opt/foodcourt

# 3. ตั้งค่า
cd /opt/foodcourt
cp .env.example .env
nano .env  # แก้ไขตามต้องการ

# 4. Deploy
chmod +x deploy.sh
./deploy.sh production
```

### วิธีที่ 2: Deploy จากเครื่อง Local

```bash
# บนเครื่อง local (Windows PowerShell)
# ต้องมี rsync หรือใช้ Git

# ใช้ deploy_remote.sh (ต้องติดตั้ง rsync และ sshpass)
chmod +x deploy_remote.sh
./deploy_remote.sh
```

## 📋 ไฟล์ที่สร้างแล้ว

- ✅ `Dockerfile` - สำหรับ build Docker image
- ✅ `docker-compose.yml` - จัดการ services (app + db + nginx)
- ✅ `.dockerignore` - ลดขนาด image
- ✅ `nginx/nginx.conf` - Reverse proxy configuration
- ✅ `deploy.sh` - Script สำหรับ deploy บน server
- ✅ `deploy_remote.sh` - Script สำหรับ deploy จาก local
- ✅ `DOCKER_DEPLOY.md` - คู่มือละเอียด

## 🔧 ตรวจสอบหลัง Deploy

```bash
# ดู status
docker compose ps

# ดู logs
docker compose logs -f app

# ทดสอบ
curl http://150.95.85.185/health
```

## 🌐 URLs

- Main: http://150.95.85.185
- Admin: http://150.95.85.185/admin
- Store POS: http://150.95.85.185/store-pos?store_id=1
- Customer: http://150.95.85.185/customer

## ⚠️ หมายเหตุ

- Database password: ตั้งค่าใน `.env` (DB_ROOT_PASSWORD)
- SECRET_KEY: เปลี่ยนเป็นค่าใหม่ที่แข็งแรง
- Ports: 80 (HTTP), 443 (HTTPS), 8000 (App direct)

