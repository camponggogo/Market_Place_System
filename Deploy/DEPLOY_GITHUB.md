# Deploy ผ่าน GitHub (Push → Server ดึงโค้ด → Docker อัตโนมัติ)

แทนการอัปโหลดด้วย SCP/rsync ให้ **push โค้ดขึ้น GitHub** แล้วให้เซิร์ฟเวอร์ **git pull และรัน Docker** อัตโนมัติ

---

## สรุปขั้นตอน

| ขั้นตอน | ทำที่ | คำอธิบาย |
|--------|--------|----------|
| 1 | เครื่องคุณ | Push โค้ดไปที่ GitHub (`git push`) |
| 2 | เซิร์ฟเวอร์ (ครั้งแรก) | โคลน repo, ใส่ `.env`, รัน deploy ครั้งแรก |
| 3 | GitHub Actions | เมื่อ push ขึ้น `main`/`master` จะ SSH เข้าเซิร์ฟเวอร์แล้วรัน `pull_and_deploy.sh` |

---

## 1. อัปโหลดโค้ดไป GitHub

### ถ้ายังไม่มี repo บน GitHub

1. สร้าง repo ใหม่ที่ https://github.com/new (ไม่ต้องใส่ README ถ้าโปรเจกต์มีอยู่แล้ว)
2. เชื่อม remote และ push:

```bash
cd /path/to/FoodCourt
git remote add origin https://github.com/YOUR_USERNAME/FoodCourt.git
git branch -M main
git push -u origin main
```

### ถ้ามี repo แล้ว

```bash
git add .
git commit -m "your message"
git push origin main
```

**หมายเหตุ:** ไฟล์ `.env` อยู่ใน `.gitignore` จะไม่ถูก push (ค่าบนเซิร์ฟเวอร์ต้องสร้างเอง)

---

## 2. ตั้งค่าเซิร์ฟเวอร์ (ทำครั้งเดียว)

SSH เข้าเซิร์ฟเวอร์ (เช่น `ssh admin@150.95.85.185`) แล้วรัน:

### 2.1 โคลนโปรเจกต์

```bash
sudo mkdir -p /opt
sudo chown $USER:$USER /opt
cd /opt
git clone https://github.com/YOUR_USERNAME/FoodCourt.git marketplace
cd marketplace
```

(ถ้า repo เป็น private ใช้ HTTPS + Personal Access Token หรือ SSH key ของเซิร์ฟเวอร์)

### 2.2 สร้างไฟล์ .env

```bash
cd /opt/marketplace/Deploy
cp .env.example .env
nano .env   # แก้ DB password, BACKEND_URL, DOMAIN (ถ้าใช้ Certbot) ฯลฯ
```

### 2.3 รัน deploy ครั้งแรก

```bash
chmod +x deploy.sh pull_and_deploy.sh
./deploy.sh production
```

หลังขั้นตอนนี้แอปจะรันใน Docker แล้ว

---

## 3. Deploy อัตโนมัติด้วย GitHub Actions

ทุกครั้งที่ `git push` ขึ้น branch `main` (หรือ `master`) GitHub Actions จะ SSH เข้าเซิร์ฟเวอร์แล้วรัน `pull_and_deploy.sh` (git pull + docker deploy)

### 3.1 ตั้งค่า Secrets ใน GitHub

ไปที่ repo บน GitHub → **Settings** → **Secrets and variables** → **Actions** → **New repository secret** แล้วเพิ่ม:

| Secret name | ค่า | หมายเหตุ |
|-------------|-----|----------|
| `DEPLOY_SSH_KEY` | เนื้อหา **private key** ทั้งก้อน (ใช้ SSH เข้าเซิร์ฟเวอร์) | ไม่ใส่ passphrase หรือใช้ key ที่ไม่มี passphrase |
| `DEPLOY_HOST` | `150.95.85.185` | IP หรือ hostname เซิร์ฟเวอร์ |
| `DEPLOY_USER` | `admin` | SSH user บนเซิร์ฟเวอร์ |

ถ้า SSH ไม่ใช้พอร์ต 22:

| Secret name | ค่า |
|-------------|-----|
| `DEPLOY_SSH_PORT` | เช่น `2222` |

ถ้าโฟลเดอร์โปรเจกต์บนเซิร์ฟเวอร์ไม่ใช่ `/opt/marketplace`:

| Secret name | ค่า |
|-------------|-----|
| `DEPLOY_REPO_DIR` | เช่น `/home/admin/marketplace` |

### 3.2 สร้าง SSH key สำหรับ GitHub Actions (แนะนำ)

บนเครื่องคุณ (หรือเซิร์ฟเวอร์):

```bash
ssh-keygen -t ed25519 -C "github-actions-deploy" -f deploy_key -N ""
```

- เอาเนื้อหา **private key** (`deploy_key`) ไปใส่ใน Secret ชื่อ `DEPLOY_SSH_KEY`
- เอา **public key** ไปใส่บนเซิร์ฟเวอร์:

```bash
# บนเซิร์ฟเวอร์ (หรือใช้ ssh-copy-id)
cat deploy_key.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

จากนั้นลบไฟล์ key ออกจากเครื่องถ้าไม่ใช้แล้ว

### 3.3 ตรวจผลหลัง push

หลัง `git push origin main` ไปที่แท็บ **Actions** ใน repo จะเห็น workflow **Deploy to Server** รันและ (ถ้าตั้งค่า secret ครบ) จะเข้าเซิร์ฟเวอร์แล้วรัน pull + deploy ให้

---

## 4. รัน deploy บนเซิร์ฟเวอร์เอง (ไม่ผ่าน GitHub Actions)

ถ้าไม่ใช้ GitHub Actions สามารถ SSH เข้าไปรันสคริปต์เองหรือตั้ง cron:

```bash
ssh admin@150.95.85.185
cd /opt/marketplace/Deploy
./pull_and_deploy.sh
```

หรือตั้ง cron ให้รันทุก 5 นาที (ตัวอย่าง):

```bash
crontab -e
# เพิ่มบรรทัด:
*/5 * * * * cd /opt/marketplace/Deploy && ./pull_and_deploy.sh >> /var/log/foodcourt-deploy.log 2>&1
```

---

## 5. โครงสร้างไฟล์ที่เกี่ยวข้อง

| ไฟล์ | คำอธิบาย |
|------|----------|
| `.github/workflows/deploy.yml` | GitHub Actions: เมื่อ push ไป main/master จะ SSH เข้าเซิร์ฟเวอร์แล้วรัน deploy |
| `Deploy/pull_and_deploy.sh` | สคริปต์บนเซิร์ฟเวอร์: `git pull` แล้วรัน `deploy.sh` (Docker) |
| `Deploy/deploy.sh` | รัน Docker Compose (build + up) |

---

## 6. ปัญหาที่พบบ่อย

- **Deploy ไม่รันหลัง push**  
  ตรวจว่า branch ที่ push คือ `main` หรือ `master` และว่า Secret ครบ (โดยเฉพาะ `DEPLOY_SSH_KEY`, `DEPLOY_HOST`, `DEPLOY_USER`)

- **Permission denied (publickey)**  
  ตรวจว่าเนื้อหาใน `DEPLOY_SSH_KEY` เป็น private key เต็มก้อน (รวมบรรทัด `-----BEGIN ... KEY-----` และ `-----END ... KEY-----`) และว่า public key ถูกเพิ่มใน `~/.ssh/authorized_keys` ของ user บนเซิร์ฟเวอร์แล้ว

- **Connection timed out**  
  ตรวจว่าเซิร์ฟเวอร์เปิดพอร์ต SSH (เช่น 22) และ firewall/security group อนุญาตจาก IP ของ GitHub (หรือใช้การเชื่อมต่อแบบอื่นตามที่ host รองรับ)
