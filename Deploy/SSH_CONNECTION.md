# การเชื่อมต่อ SSH สำหรับ Deploy

สคริปต์ deploy ใช้ค่าเริ่มต้นดังนี้ (แก้ได้ในสคริปต์หรือส่งพารามิเตอร์):

| ค่า | ค่าเริ่มต้น | คำอธิบาย |
|-----|-------------|----------|
| โฮสต์ | **150.95.85.185** | IP เซิร์ฟเวอร์ |
| ผู้ใช้ | **admin** | SSH user |
| โฟลเดอร์บนเซิร์ฟเวอร์ | /opt/marketplace | ที่เก็บโปรเจกต์ |
| พอร์ต SSH | 22 | ถ้าเซิร์ฟเวอร์ใช้พอร์ตอื่น ต้องกำหนด |

รหัสผ่านจะ **ไม่** เก็บในสคริปต์ — ระบบจะถามรหัสผ่านเมื่อเชื่อมต่อ (หรือใช้ SSH key)

---

## แก้ error: Connection timed out

ข้อความ `connect to host ... port 22: Connection timed out` หมายความว่าเชื่อมต่อ TCP ไปพอร์ต 22 ไม่ได้ มักเกิดจาก:

### 1. Firewall / Security Group บล็อกพอร์ต 22

- **บนเซิร์ฟเวอร์ (Linux):** เปิดพอร์ต 22 (หรือพอร์ต SSH ที่ใช้)
  ```bash
  # ตัวอย่าง (ufw)
  sudo ufw allow 22
  sudo ufw reload
  ```
- **Cloud (AWS/GCP/Azure ฯลฯ):** ใน Security Group / Firewall rules อนุญาต Inbound **TCP 22** จาก IP ของคุณ (หรือ 0.0.0.0/0 ถ้าต้องการให้เข้าจากทุกที่)

### 2. SSH รันอยู่พอร์ตอื่น (ไม่ใช่ 22)

ถ้าเซิร์ฟเวอร์ใช้พอร์ตอื่น (เช่น 2222):

- **Bash (deploy_to_campong.sh):**
  ```bash
  REMOTE_SSH_PORT=2222 ./Deploy/deploy_to_campong.sh
  ```
- **PowerShell (deploy_to_campong.ps1):**
  ```powershell
  .\Deploy\deploy_to_campong.ps1 -RemoteSshPort 2222
  ```

### 3. ตรวจสอบว่า SSH ฟังอยู่และพอร์ตเปิด

จากเครื่องอื่น (หรือจากเซิร์ฟเวอร์เอง):

```bash
# ทดสอบว่าพอร์ต 22 เปิดหรือไม่
nc -zv 150.95.85.185 22
# หรือ
telnet 150.95.85.185 22
```

ถ้าเชื่อมต่อได้ แสดงว่าพอร์ตเปิด จากนั้นลอง `ssh admin@150.95.85.185` อีกครั้ง

### 4. Windows: config หรือไฟล์ config หาย

ถ้าเห็น `Failed to open file C:/Users/.../ssh_config error:2` — บางทีโฟลเดอร์หรือไฟล์ config ยังไม่มี ไม่จำเป็นต้องมีไฟล์ config ก็เชื่อมต่อได้ แค่สร้างโฟลเดอร์ถ้าต้องการใช้ key หรือ config ภายหลัง:

```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.ssh"
```

---

## ใช้รหัสผ่านหรือ SSH Key

- **รหัสผ่าน:** รันสคริปต์ deploy แล้วใส่รหัสผ่านเมื่อถูกถาม (ไม่ควรใส่รหัสผ่านในสคริปต์)
- **SSH Key (แนะนำ):** สร้าง key แล้วเอา public key ไปใส่ใน `~/.ssh/authorized_keys` บนเซิร์ฟเวอร์ จะได้ไม่ต้องใส่รหัสผ่านทุกครั้ง
