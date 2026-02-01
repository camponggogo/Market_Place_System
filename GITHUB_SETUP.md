# ขึ้น GitHub - Market_Place_System

## สิ่งที่ทำแล้วในโปรเจกต์

- ตั้งชื่อโปรเจกต์ใน README: **Market_Place_System**
- คำอธิบาย: **ระบบจัดการตลาดนัด Onlinehelp**
- สร้าง commit แรกแล้ว

---

## ขั้นตอน: สร้าง Repo บน GitHub แล้ว Push

### 1. สร้าง Repository บน GitHub

1. เปิด https://github.com/new (ต้องล็อกอินด้วยบัญชี **campong@gmail.com**)
2. ตั้งค่า:
   - **Repository name:** `Market_Place_System`
   - **Description:** `ระบบจัดการตลาดนัด Onlinehelp`
   - เลือก **Public** (หรือ Private ตามต้องการ)
   - **อย่าติ๊ก** "Add a README" (เพราะมีอยู่แล้วในโปรเจกต์)
3. กด **Create repository**

### 2. เชื่อม Remote และ Push

เปิด PowerShell ในโฟลเดอร์โปรเจกต์ (`D:\Projects\FoodCourt`) แล้วรัน:

**ถ้า GitHub username ของคุณคือ `campong`:**

```powershell
git remote add origin https://github.com/campong/Market_Place_System.git
git branch -M main
git push -u origin main
```

**ถ้า username เป็นอย่างอื่น** ให้แทนที่ `campong` ด้วย username จริงของคุณ เช่น:

```powershell
git remote add origin https://github.com/YOUR_USERNAME/Market_Place_System.git
git branch -M main
git push -u origin main
```

### 3. ใส่รหัสผ่าน (ถ้าถูกถาม)

- ถ้าใช้ HTTPS: ใช้ **Personal Access Token** แทนรหัสผ่านบัญชี (Settings → Developer settings → Personal access tokens)
- หรือใช้ **Git Credential Manager** ที่ Windows แนะนำ

---

หลังจาก push เสร็จ Repo จะอยู่ที่:

**https://github.com/YOUR_USERNAME/Market_Place_System**

และ Description จะแสดงเป็น: **ระบบจัดการตลาดนัด Onlinehelp**
