#!/bin/sh
# ต่ออายุใบรับรอง Let's Encrypt (รันจากโฟลเดอร์ Deploy)
# ใช้กับ cron: 0 3 * * * cd /path/to/FoodCourt/Deploy && ./certbot-renew.sh

set -e
cd "$(dirname "$0")"

docker compose -f docker-compose.yml run --rm certbot renew \
  --webroot -w /var/www/certbot --quiet

# Reload nginx ถ้ามี container ทำงานอยู่
docker compose -f docker-compose.yml exec -T nginx nginx -s reload 2>/dev/null || true
