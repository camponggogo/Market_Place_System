# Production Deployment Guide
## สำหรับ Scale: ~1000 users/day, ~200 stores/day

## 📋 สิ่งที่ต้องเตรียม

### 1. Server Requirements
- **CPU**: 2-4 cores
- **RAM**: 4-8 GB
- **Storage**: 20-50 GB
- **OS**: Ubuntu 20.04+ / Debian 11+ / CentOS 8+

### 2. Software Requirements
- Python 3.9+
- MariaDB/MySQL 10.5+
- Nginx (แนะนำ)
- SSL Certificate (Let's Encrypt)

---

## 🚀 ขั้นตอนการ Deploy

### Step 1: ติดตั้ง Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3 python3-pip python3-venv python3-dev -y
sudo apt install mariadb-server mariadb-client -y
sudo apt install nginx -y
sudo apt install certbot python3-certbot-nginx -y
```

### Step 2: Clone และ Setup Project

```bash
# Clone project
cd /var/www
git clone <your-repo-url> foodcourt
cd foodcourt

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Configure Database

```bash
# Create database
sudo mysql -u root -p
```

```sql
CREATE DATABASE foodcourt CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'foodcourt'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON foodcourt.* TO 'foodcourt'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### Step 4: Configure Application

```bash
# Copy config files
cp .env.example .env
cp config.ini.example config.ini

# Edit config.ini
nano config.ini
```

```ini
[DATABASE]
DB_HOST=localhost
DB_PORT=3306
DB_NAME=foodcourt
DB_USER=foodcourt
DB_PASSWORD=your_secure_password

[BACKEND]
BACKEND_URL=https://your-domain.com
DEBUG=False
```

```bash
# Edit .env
nano .env
```

```env
ENABLE_DOCS=false
ALLOWED_ORIGINS=https://your-domain.com,https://www.your-domain.com
```

### Step 5: Initialize Database

```bash
python scripts/init_db.py
```

### Step 6: Setup Gunicorn Service

```bash
# Create systemd service
sudo nano /etc/systemd/system/foodcourt.service
```

```ini
[Unit]
Description=Food Court Management System
After=network.target mariadb.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/foodcourt
Environment="PATH=/var/www/foodcourt/venv/bin"
ExecStart=/var/www/foodcourt/venv/bin/gunicorn main:app -c gunicorn_config.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable foodcourt
sudo systemctl start foodcourt
sudo systemctl status foodcourt
```

### Step 7: Setup Nginx

```bash
# Copy nginx config
sudo cp nginx.conf.example /etc/nginx/sites-available/foodcourt

# Edit config
sudo nano /etc/nginx/sites-available/foodcourt
# แก้ไข your-domain.com เป็น domain ของคุณ

# Enable site
sudo ln -s /etc/nginx/sites-available/foodcourt /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Step 8: Setup SSL (Let's Encrypt)

```bash
# Get SSL certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Auto-renewal (already configured by certbot)
sudo certbot renew --dry-run
```

---

## 🔒 Security Checklist

- [ ] เปลี่ยน default passwords
- [ ] ตั้งค่า firewall (UFW)
- [ ] เปิดเฉพาะ ports ที่จำเป็น (80, 443)
- [ ] ตั้งค่า rate limiting
- [ ] เปิดใช้งาน SSL/TLS
- [ ] ตั้งค่า security headers
- [ ] ปิด API docs ใน production (`ENABLE_DOCS=false`)
- [ ] ระบุ allowed origins ใน CORS
- [ ] ตั้งค่า database user permissions
- [ ] Enable database backups

---

## 📊 Monitoring

### Check Service Status

```bash
# Gunicorn service
sudo systemctl status foodcourt

# Nginx
sudo systemctl status nginx

# MariaDB
sudo systemctl status mariadb
```

### View Logs

```bash
# Application logs
sudo journalctl -u foodcourt -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Application errors
tail -f /var/log/foodcourt/error.log
```

### Performance Monitoring

```bash
# System resources
htop

# Database connections
sudo mysql -u root -p -e "SHOW PROCESSLIST;"

# Nginx status
curl http://localhost/nginx_status
```

---

## 🔧 Maintenance

### Update Application

```bash
cd /var/www/foodcourt
source venv/bin/activate
git pull
pip install -r requirements.txt
sudo systemctl restart foodcourt
```

### Database Backup

```bash
# Create backup script
sudo nano /usr/local/bin/backup-foodcourt.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/foodcourt"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR
mysqldump -u foodcourt -p'your_password' foodcourt > $BACKUP_DIR/foodcourt_$DATE.sql
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
```

```bash
# Make executable
sudo chmod +x /usr/local/bin/backup-foodcourt.sh

# Add to crontab (daily at 2 AM)
sudo crontab -e
# Add: 0 2 * * * /usr/local/bin/backup-foodcourt.sh
```

---

## 🚨 Troubleshooting

### Service won't start

```bash
# Check logs
sudo journalctl -u foodcourt -n 50

# Check permissions
ls -la /var/www/foodcourt
sudo chown -R www-data:www-data /var/www/foodcourt
```

### Database connection error

```bash
# Test connection
mysql -u foodcourt -p foodcourt

# Check MariaDB status
sudo systemctl status mariadb
```

### High memory usage

```bash
# Reduce workers in gunicorn_config.py
workers = 4  # แทนที่จะใช้ cpu_count * 2
```

---

## 📈 Performance Tuning

### สำหรับ Scale นี้ (~1000 users/day):

1. **Gunicorn Workers**: 4-8 workers
2. **Database Pool**: 10-20 connections
3. **Nginx**: Enable gzip, caching
4. **CDN**: สำหรับ static files (optional)

### Expected Performance:

- **Response Time**: < 200ms (average)
- **Concurrent Users**: 50-100
- **Requests/Second**: 10-20
- **Database Queries**: Optimized with indexes

---

## 🔗 Useful Commands

```bash
# Restart services
sudo systemctl restart foodcourt
sudo systemctl restart nginx

# Check service status
sudo systemctl status foodcourt nginx mariadb

# View real-time logs
sudo journalctl -u foodcourt -f

# Test configuration
sudo nginx -t
gunicorn main:app -c gunicorn_config.py --check-config
```

---

## 📞 Support

หากมีปัญหา:
1. ตรวจสอบ logs
2. ตรวจสอบ service status
3. ตรวจสอบ database connection
4. ตรวจสอบ firewall rules

