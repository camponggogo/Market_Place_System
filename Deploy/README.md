# Deploy/

ไฟล์สำหรับ **Docker และการ Deploy**

- **Dockerfile** – Build image จากโฟลเดอร์ `code/`
- **docker-compose.yml** – กำหนด services (db, app, nginx)
- **nginx/** – config Nginx
- **deploy.sh**, **deploy_remote.ps1** ฯลฯ – สคริปต์ deploy
- **DOCKER_DEPLOY.md** – คู่มือ deploy ด้วย Docker

## รัน Docker (จาก root โปรเจกต์)

```bash
docker compose -f Deploy/docker-compose.yml up -d
```

Build context คือ root โปรเจกต์ (มีโฟลเดอร์ `code/`, `Run/`) เพื่อให้ Dockerfile copy `code/` ได้
