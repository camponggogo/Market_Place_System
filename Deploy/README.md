# Deploy/

ไฟล์สำหรับ **Docker และการ Deploy**

- **Dockerfile** – Build image จากโฟลเดอร์ `code/` (แอปรันบน **port 639**)
- **docker-compose.yml** – กำหนด services (db, app, nginx); แอป map port **639**
- **nginx/** – config Nginx (proxy ไปที่ app:639)
- **deploy.sh**, **deploy_remote.ps1** ฯลฯ – สคริปต์ deploy
- **deploy_to_campong.sh** (Bash) / **deploy_to_campong.ps1** (PowerShell) – copy ไป 150.95.85.185 (user: admin) ด้วย rsync/scp แล้วรัน Docker ทันที (จาก root โปรเจกต์)
- **SSH_CONNECTION.md** – ตั้งค่า SSH (โฮสต์/user/พอร์ต) และแก้ปัญหา Connection timed out
- **DEPLOY_GITHUB.md** – Deploy ผ่าน GitHub: push โค้ดขึ้น GitHub แล้วให้เซิร์ฟเวอร์ git pull + รัน Docker อัตโนมัติ (ด้วย GitHub Actions หรือสคริปต์ `pull_and_deploy.sh`)
- **DOCKER_DEPLOY.md** – คู่มือ deploy ด้วย Docker
- **DEV_ON_CLOUD.md** – พัฒนาบน Cloud ผ่าน SSH, Docker พอร์ต 639, HTTPS จริง (ไม่พึ่ง ngrok)
- **CERTBOT.md** – ใช้ Certbot (Let's Encrypt) สำหรับ HTTPS; ตั้ง `DOMAIN` + `CERTBOT_EMAIL` ใน `.env` แล้วรัน `./certbot-init.sh`

## รัน Docker (จาก root โปรเจกต์)

```bash
docker compose -f Deploy/docker-compose.yml up -d
```

แอปจะ listen ที่ **port 639** (ใน container และ map ออก host โดย default). Build context คือ root โปรเจกต์ (มีโฟลเดอร์ `code/`, `Run/`)

### HTTPS ด้วย Certbot

ตั้ง `DOMAIN` และ `CERTBOT_EMAIL` ใน `.env` จากนั้นรัน `./certbot-init.sh` ในโฟลเดอร์ Deploy (ดู **CERTBOT.md**)
