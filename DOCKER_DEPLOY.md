# คู่มือการ Deploy ด้วย Docker

## 📋 ข้อกำหนดเบื้องต้น

- Server: `150.95.85.185`
- SSH Access: `root@150.95.85.185`
- Password: `P@ssw0rd@dev`
- Docker และ Docker Compose ต้องติดตั้งแล้วบน server

## 🚀 ขั้นตอนการ Deploy

### 1. เชื่อมต่อ Server

```bash
ssh root@150.95.85.185
# Password: P@ssw0rd@dev
```

### 2. ติดตั้ง Docker และ Docker Compose (ถ้ายังไม่มี)

```bash
# Update system
apt-get update && apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt-get install -y docker-compose-plugin

# หรือใช้ docker-compose แบบ standalone
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Start Docker service
systemctl start docker
systemctl enable docker

# Verify installation
docker --version
docker compose version
```

### 3. อัปโหลด Project ไปยัง Server

**วิธีที่ 1: ใช้ Git (แนะนำ)**

```bash
# บน server
cd /opt
git clone <your-repo-url> foodcourt
cd foodcourt
```

**วิธีที่ 2: ใช้ SCP จากเครื่อง local**

```bash
# บนเครื่อง local (Windows PowerShell)
scp -r D:\Projects\FoodCourt root@150.95.85.185:/opt/foodcourt
```

**วิธีที่ 3: ใช้ rsync**

```bash
# บนเครื่อง local
rsync -avz --exclude 'venv' --exclude '__pycache__' --exclude '.git' D:\Projects\FoodCourt\ root@150.95.85.185:/opt/foodcourt/
```

### 4. ตั้งค่า Environment Variables

```bash
# บน server
cd /opt/foodcourt

# สร้างไฟล์ .env จาก .env.example
cp .env.example .env

# แก้ไข .env ตามต้องการ
nano .env
```

**ตัวอย่าง .env:**

```env
# Database
DB_ROOT_PASSWORD=P@ssw0rd@dev
DB_NAME=foodcourt
DB_USER=foodcourt_user
DB_PASSWORD=foodcourt_pass
DB_PORT=3306

# Application
APP_PORT=8000
BACKEND_URL=http://150.95.85.185
SECRET_KEY=your-very-strong-secret-key-here-change-this
DEBUG=false
ENABLE_DOCS=false

# CORS
ALLOWED_ORIGINS=*

# Nginx
NGINX_HTTP_PORT=80
NGINX_HTTPS_PORT=443
```

### 5. Deploy ด้วย Docker Compose

```bash
# ให้สิทธิ์ execute
chmod +x deploy.sh

# รัน deployment script
./deploy.sh production
```

**หรือใช้ docker compose โดยตรง:**

```bash
# Build และ start services
docker compose build
docker compose up -d

# ดู logs
docker compose logs -f

# ตรวจสอบ status
docker compose ps
```

### 6. ตรวจสอบการทำงาน

```bash
# ตรวจสอบ containers
docker compose ps

# ตรวจสอบ logs
docker compose logs app
docker compose logs db
docker compose logs nginx

# ทดสอบ health check
curl http://localhost:8000/health
curl http://localhost/health
```

### 7. เปิด Firewall Ports (ถ้าจำเป็น)

```bash
# Ubuntu/Debian
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8000/tcp
ufw reload

# CentOS/RHEL
firewall-cmd --permanent --add-port=80/tcp
firewall-cmd --permanent --add-port=443/tcp
firewall-cmd --permanent --add-port=8000/tcp
firewall-cmd --reload
```

## 🔧 คำสั่งที่มีประโยชน์

### ดู Logs

```bash
# ทั้งหมด
docker compose logs -f

# เฉพาะ app
docker compose logs -f app

# เฉพาะ database
docker compose logs -f db

# เฉพาะ nginx
docker compose logs -f nginx
```

### Restart Services

```bash
# Restart ทั้งหมด
docker compose restart

# Restart เฉพาะ service
docker compose restart app
```

### Stop และ Start

```bash
# Stop
docker compose stop

# Start
docker compose start

# Stop และลบ containers
docker compose down

# Stop และลบ containers + volumes (ระวัง! จะลบข้อมูล)
docker compose down -v
```

### เข้าไปใน Container

```bash
# เข้าไปใน app container
docker exec -it foodcourt_app bash

# เข้าไปใน database container
docker exec -it foodcourt_db bash

# เข้า MySQL
docker exec -it foodcourt_db mysql -u root -p
```

### Update Application

```bash
# Pull code ใหม่ (ถ้าใช้ Git)
git pull

# Rebuild และ restart
docker compose build --no-cache app
docker compose up -d app
```

## 🗄️ Database Management

### Backup Database

```bash
# Backup
docker exec foodcourt_db mysqldump -u root -p${DB_ROOT_PASSWORD} foodcourt > backup_$(date +%Y%m%d_%H%M%S).sql

# หรือใช้ docker compose
docker compose exec db mysqldump -u root -p${DB_ROOT_PASSWORD} foodcourt > backup.sql
```

### Restore Database

```bash
# Restore
docker exec -i foodcourt_db mysql -u root -p${DB_ROOT_PASSWORD} foodcourt < backup.sql
```

## 🔒 Security

### เปลี่ยน Password

```bash
# เปลี่ยน root password ใน database
docker exec -it foodcourt_db mysql -u root -p
# แล้วรัน: ALTER USER 'root'@'localhost' IDENTIFIED BY 'new_password';

# อัปเดต .env และ restart
docker compose restart db
```

### SSL/HTTPS (ถ้าต้องการ)

1. วาง SSL certificates ใน `nginx/ssl/`
2. แก้ไข `nginx/nginx.conf` เพื่อ uncomment HTTPS server block
3. Restart nginx: `docker compose restart nginx`

## 📊 Monitoring

### ดู Resource Usage

```bash
# ดู stats
docker stats

# ดู disk usage
docker system df
```

### Health Checks

```bash
# Application health
curl http://localhost:8000/health

# Database health
docker compose exec db mysqladmin ping -h localhost -u root -p
```

## 🐛 Troubleshooting

### Container ไม่ start

```bash
# ดู logs
docker compose logs app

# ตรวจสอบ configuration
docker compose config
```

### Database Connection Error

```bash
# ตรวจสอบ database container
docker compose ps db

# ตรวจสอบ database logs
docker compose logs db

# ทดสอบ connection
docker compose exec app python -c "from app.database import engine; engine.connect()"
```

### Port Already in Use

```bash
# ตรวจสอบ port ที่ใช้
netstat -tulpn | grep :80
netstat -tulpn | grep :8000

# เปลี่ยน port ใน docker-compose.yml หรือ .env
```

## 📝 Notes

- Database data จะถูกเก็บใน Docker volume `db_data`
- Application logs อยู่ใน Docker volume `app_logs`
- Nginx logs อยู่ใน Docker volume `nginx_logs`
- ไฟล์ config.ini จะถูก mount จาก host เพื่อให้แก้ไขได้ง่าย

## 🔗 URLs

หลังจาก deploy สำเร็จ:

- Main: http://150.95.85.185
- Admin Dashboard: http://150.95.85.185/admin
- Store POS: http://150.95.85.185/store-pos?store_id=1
- Customer: http://150.95.85.185/customer
- Health Check: http://150.95.85.185/health

