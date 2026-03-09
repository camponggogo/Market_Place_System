#!/bin/bash
# Copy โปรเจกต์ไป m.campong.co.th ด้วย rsync/scp แล้วรัน Docker ทันที
# ใช้: จาก root โปรเจกต์ (FoodCourt) → ./Deploy/deploy_to_campong.sh
# หรือ: cd Deploy && ./deploy_to_campong.sh (จะขึ้นไปที่ parent เป็น project root)

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# โปรเจกต์ root = parent ของ Deploy
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

REMOTE_HOST="${REMOTE_HOST:-150.95.85.185}"
REMOTE_USER="${REMOTE_USER:-admin}"
REMOTE_DIR="${REMOTE_DIR:-/opt/marketplace}"
# พอร์ต SSH (ถ้าไม่ใช่ 22 เช่น เซิร์ฟเวอร์ใช้ 2222 ให้ตั้ง REMOTE_SSH_PORT=2222)
REMOTE_SSH_PORT="${REMOTE_SSH_PORT:-22}"
SSH_OPTS=(-o StrictHostKeyChecking=no -o ConnectTimeout=15)
[ "$REMOTE_SSH_PORT" != "22" ] && SSH_OPTS=(-p "$REMOTE_SSH_PORT" "${SSH_OPTS[@]}")
# สำหรับ rsync -e ต้องส่งเป็นสตริง
RSYNC_SSH="ssh -o StrictHostKeyChecking=no -o ConnectTimeout=15"
[ "$REMOTE_SSH_PORT" != "22" ] && RSYNC_SSH="ssh -p $REMOTE_SSH_PORT $RSYNC_SSH"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=========================================="
echo "Deploy to m.campong.co.th (Docker)"
echo "=========================================="
echo "Project root: $PROJECT_ROOT"
echo "Target: ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR} (SSH port: ${REMOTE_SSH_PORT})"
echo "=========================================="

# Excludes (ไม่ copy เข้า server)
EXCLUDES=(
  --exclude='.git'
  --exclude='venv'
  --exclude='__pycache__'
  --exclude='*.pyc'
  --exclude='.pytest_cache'
  --exclude='htmlcov'
  --exclude='*.db'
  --exclude='.env'
)

# 1) Copy ไฟล์ไปเซิร์ฟเวอร์ (code, Run, Deploy ใต้ REMOTE_DIR)
if command -v rsync &>/dev/null; then
  echo -e "${GREEN}Using rsync...${NC}"
  ssh "${SSH_OPTS[@]}" "${REMOTE_USER}@${REMOTE_HOST}" "mkdir -p ${REMOTE_DIR}"
  rsync -avz --progress "${EXCLUDES[@]}" -e "$RSYNC_SSH" \
    "$PROJECT_ROOT/code/" "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/code/"
  rsync -avz --progress "${EXCLUDES[@]}" -e "$RSYNC_SSH" \
    "$PROJECT_ROOT/Run/" "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/Run/"
  rsync -avz --progress "${EXCLUDES[@]}" -e "$RSYNC_SSH" \
    "$PROJECT_ROOT/Deploy/" "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/Deploy/"
else
  echo -e "${YELLOW}rsync not found, using tar over ssh...${NC}"
  tar cf - \
    --exclude='.git' \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.pytest_cache' \
    --exclude='htmlcov' \
    --exclude='.env' \
    -C "$PROJECT_ROOT" \
    code Run Deploy \
  | ssh "${SSH_OPTS[@]}" "${REMOTE_USER}@${REMOTE_HOST}" "mkdir -p ${REMOTE_DIR} && cd ${REMOTE_DIR} && tar xf -"
fi

# Copy .env.example ถ้ามี (ให้ remote สร้าง .env ได้)
if [ -f "$PROJECT_ROOT/.env.example" ]; then
  scp "${SSH_OPTS[@]}" "$PROJECT_ROOT/.env.example" "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/Deploy/.env.example" 2>/dev/null || true
fi

# 2) สร้าง .env บน remote ถ้ายังไม่มี แล้วรัน Docker
echo -e "${GREEN}Starting Docker on remote...${NC}"
ssh "${SSH_OPTS[@]}" "${REMOTE_USER}@${REMOTE_HOST}" "set -e
  cd ${REMOTE_DIR}/Deploy
  [ -f .env ] || { [ -f .env.example ] && cp .env.example .env; } || true
  chmod +x deploy.sh certbot-init.sh certbot-renew.sh 2>/dev/null || true
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    docker compose -f docker-compose.yml down 2>/dev/null || true
    docker compose -f docker-compose.yml build --no-cache
    docker compose -f docker-compose.yml up -d
    echo 'Waiting for services...'
    sleep 15
    docker compose -f docker-compose.yml ps
  else
    ./deploy.sh production
  fi
"

echo ""
echo -e "${GREEN}=========================================="
echo "Deploy done."
echo -e "==========================================${NC}"
echo "URL: https://${REMOTE_HOST}:639 (or https://m.campong.co.th:639)"
echo "Health: https://${REMOTE_HOST}:639/health"
echo ""
echo "View logs: ssh ${SSH_OPTS[*]} ${REMOTE_USER}@${REMOTE_HOST} 'cd ${REMOTE_DIR}/Deploy && docker compose logs -f'"
echo ""
