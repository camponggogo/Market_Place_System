#!/bin/bash
# รันบนเซิร์ฟเวอร์: ดึงโค้ดล่าสุดจาก GitHub แล้วรัน Docker deploy
# ใช้โดย: 1) SSH เข้าไปรันเอง 2) Cron 3) GitHub Actions
# ต้องมี: git, docker, docker compose และ repo โคลนไว้แล้วที่ REPO_DIR

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=========================================="
echo "Pull & Deploy (GitHub → Docker)"
echo "=========================================="
echo "Repo: $REPO_ROOT"
echo ""

# ไม่ overwrite .env ถ้ามีอยู่แล้ว (เก็บค่าบนเซิร์ฟเวอร์)
if [ ! -f "$SCRIPT_DIR/.env" ] && [ -f "$SCRIPT_DIR/.env.example" ]; then
  cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
  echo -e "${YELLOW}Created .env from .env.example — please edit with your values.${NC}"
fi

# ดึงโค้ดล่าสุด (branch ตามที่เซิร์ฟเวอร์ตั้งไว้ มักเป็น main)
echo -e "${GREEN}Git pull...${NC}"
git fetch origin
BRANCH=$(git branch --show-current)
if [ -z "$BRANCH" ]; then BRANCH=main; fi
git pull origin "$BRANCH" --rebase || git pull origin main --rebase || git pull --rebase || true

# รัน deploy ในโฟลเดอร์ Deploy
echo -e "${GREEN}Running Docker deploy...${NC}"
cd "$SCRIPT_DIR"
chmod +x deploy.sh 2>/dev/null || true
./deploy.sh production

echo ""
echo -e "${GREEN}=========================================="
echo "Deploy completed."
echo -e "==========================================${NC}"
