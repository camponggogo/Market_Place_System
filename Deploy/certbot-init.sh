#!/bin/sh
# ขอใบรับรอง Let's Encrypt ครั้งแรก (ต้องมี DOMAIN และ CERTBOT_EMAIL ใน .env หรือส่งเป็นอาร์กิวเมนต์)
# ใช้: ./certbot-init.sh
# หรือ: ./certbot-init.sh your-domain.com your@email.com

set -e
cd "$(dirname "$0")"

# โหลด .env ถ้ามี
if [ -f ../.env ]; then
  set -a
  . ../.env
  set +a
fi

DOMAIN="${1:-$DOMAIN}"
EMAIL="${2:-$CERTBOT_EMAIL}"

if [ -z "$DOMAIN" ] || [ -z "$EMAIL" ]; then
  echo "Usage: $0 [DOMAIN] [EMAIL]"
  echo "  or set DOMAIN and CERTBOT_EMAIL in .env"
  echo "Example: $0 example.com admin@example.com"
  exit 1
fi

echo "Requesting certificate for $DOMAIN (email: $EMAIL)"
docker compose -f docker-compose.yml run --rm certbot certonly \
  --webroot \
  -w /var/www/certbot \
  -d "$DOMAIN" \
  --email "$EMAIL" \
  --agree-tos \
  --non-interactive \
  --force-renewal

echo "Certificate obtained. Reloading nginx..."
docker compose -f docker-compose.yml exec nginx nginx -s reload 2>/dev/null || true
echo "Done. HTTPS should now serve the new certificate for $DOMAIN"
