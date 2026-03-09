# Certbot (Let's Encrypt) ในโปรเจกต์ FoodCourt

โปรเจกต์รองรับ **Certbot** สำหรับขอและต่ออายุใบรับรอง SSL จาก Let's Encrypt โดยใช้วิธี **webroot** ผ่าน Nginx (ไม่ต้องหยุด Nginx ตอนขอ cert)

## สิ่งที่ต้องมี

- **โดเมน** ชี้ A record มาที่ IP ของเซิร์ฟเวอร์
- **พอร์ต 80 และ 443** เปิดจากอินเทอร์เน็ต
- กำหนด **DOMAIN** และ **CERTBOT_EMAIL** (ใน `.env` หรือส่งตอนรันสคริปต์)

## การตั้งค่า

### 1. ตั้งค่าใน `.env` (ที่ root โปรเจกต์ หรือในโฟลเดอร์ Deploy)

```env
DOMAIN=your-domain.com
CERTBOT_EMAIL=admin@your-domain.com
```

### 2. รัน Stack

```bash
cd Deploy
docker compose -f docker-compose.yml up -d
```

ถ้า `DOMAIN` ถูกตั้งค่า Nginx จะใช้เทมเพลตที่รองรับ HTTPS และโฟลเดอร์ `.well-known/acme-challenge/` สำหรับ Certbot  
ครั้งแรกที่ยังไม่มี cert จริง ระบบจะสร้าง self-signed ชั่วคราวให้ Nginx ขึ้นได้

### 3. ขอใบรับรองครั้งแรก

จากโฟลเดอร์ `Deploy`:

```bash
# ใช้ค่า DOMAIN และ CERTBOT_EMAIL จาก .env
./certbot-init.sh

# หรือระบุโดเมนกับอีเมลเอง
./certbot-init.sh your-domain.com admin@example.com
```

หรือรัน Certbot โดยตรง:

```bash
docker compose -f docker-compose.yml run --rm certbot certonly \
  --webroot -w /var/www/certbot \
  -d your-domain.com \
  --email admin@example.com \
  --agree-tos --non-interactive
```

จากนั้น reload Nginx:

```bash
docker compose -f docker-compose.yml exec nginx nginx -s reload
```

### 4. ต่ออายุใบรับรอง (Renew)

ใบรับรอง Let's Encrypt ใช้ได้ 90 วัน ควรต่ออายุอัตโนมัติด้วย cron:

```bash
# ต่ออายุ (จะต่อเมื่อใกล้หมดอายุเท่านั้น)
docker compose -f docker-compose.yml run --rm certbot renew --webroot -w /var/www/certbot

# reload Nginx หลังต่ออายุ
docker compose -f docker-compose.yml exec nginx nginx -s reload
```

ตัวอย่าง cron (รันทุกวันเวลา 03:00):

```cron
0 3 * * * cd /path/to/FoodCourt/Deploy && docker compose -f docker-compose.yml run --rm certbot renew --webroot -w /var/www/certbot -q && docker compose -f docker-compose.yml exec nginx nginx -s reload
```

## โครงสร้างที่เกี่ยวข้อง

| ส่วน | คำอธิบาย |
|------|-----------|
| `nginx/nginx.conf.template` | เทมเพลต Nginx ที่ใช้เมื่อมี `DOMAIN` (มี HTTPS + location `.well-known`) |
| `nginx/entrypoint-certbot.sh` | สร้าง dummy cert ถ้ายังไม่มี, แทนที่ `${DOMAIN}` แล้วสตาร์ท Nginx |
| `certbot-init.sh` | สคริปต์ขอ cert ครั้งแรกและ reload Nginx |
| Volumes `certbot_www`, `certbot_etc` | เก็บ webroot ของ ACME และไฟล์ cert ของ Certbot |

## ไม่ใช้ Certbot (ไม่มี DOMAIN)

ถ้าไม่ตั้ง `DOMAIN` ใน `.env` Nginx จะใช้ config เดิม (`nginx.conf` เป็น `nginx-default.conf`) แบบ HTTP เท่านั้น ไม่มีบล็อก HTTPS และไม่ใช้ Certbot

## Stripe Webhook

เมื่อใช้ HTTPS จาก Certbot แล้ว ควรตั้งค่า Stripe Webhook URL เป็น:

- `https://your-domain.com/api/payment-callback/webhook/stripe`

และใส่ **Signing secret** จาก Stripe Dashboard ใน `config.ini` หรือ env (`STRIPE_WEBHOOK_SECRET`)
