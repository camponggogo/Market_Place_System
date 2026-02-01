# Hardware – Micro POS (Market_Place_System)

เฟิร์มแวร์สำหรับ **D1 MINI PRO ESP-8266EX** ใช้เป็น Micro POS ฮาร์ดแวร์ล้วน เรียก API ของ Market_Place_System

## อุปกรณ์

- **บอร์ด:** D1 MINI PRO (ESP-8266EX)
- **จอฝั่งคนขาย:** KMR1441_SPI V2 1.44" 128x128 SPI (ST7735)
- **จอฝั่งลูกค้า:** KMR1441_SPI V2 1.44" 128x128 SPI (ST7735)
- **คีย์แพด:** MPR121 Capacitive (I2C) – แมปปุ่ม [0=del, 1=7, 2=4, 3=1, 4=0, 5=8, 6=5, 7=2, 8=enter, 9=9, 10=6, 11=3]
- **QR Reader:** Serial (SoftwareSerial 9600) – อ่านค่าส่งเข้าเครื่อง
- **Config / Debug:** Serial 115200 (USB)
- **ตัวเลือก:** Serial 9600 ไป ESC/POS เครื่องพิมพ์ใบเสร็จ / Cash Drawer

## การต่อสาย (Pinout)

### จอ SPI ทั้งสอง (TFT1, TFT2)

จอ ST7735 ต้องต่อ **ครบทุกขา** ด้านล่าง ถ้าขาดอาจจอขาว/มืด/ไม่ขึ้นภาพ

| สายจอ (ขาจอภาพ) | D1 Mini Pro | GPIO | หมายเหตุ |
|------------------|-------------|------|----------|
| **VCC**          | 3.3V        | -    | ใช้ 3.3V เท่านั้น (ห้าม 5V) |
| **GND**          | GND         | -    | |
| **CS** (จอ 1)    | D8          | 15   | TFT1 (Seller) – KMR1441 V2 128x128 |
| **CS** (จอ 2)    | D4          | 2    | TFT2 (Customer) – KMR1441 V2 128x128 |
| **DC** (หรือ A0) | D3          | 0    | ใช้ร่วมกันทั้งสองจอได้ |
| **RST** (Reset)  | D0          | 16   | ใช้ร่วมกันทั้งสองจอได้ |
| **MOSI** (DIN)   | D7          | 13   | ข้อมูล SPI – **ต้องต่อ** จอทั้งสองใช้ร่วมกัน |
| **SCK** (CLK)    | D5          | 14   | นาฬิกา SPI – **ต้องต่อ** จอทั้งสองใช้ร่วมกัน |
| **BL** (Backlight)| 3.3V        | -    | **จำเป็น**: ต่อขา BL ของจอไป 3.3V ถ้าไม่ต่ออาจจอมืดหรือขาว |

- TFT1 (Seller):  CS=D8, DC=D3, RST=D0, MOSI=D7, SCK=D5, VCC, GND, **BL→3.3V**
- TFT2 (Customer): CS=D4, DC=D3, RST=D0, MOSI=D7, SCK=D5, VCC, GND, **BL→3.3V**

### อื่นๆ

| หน้าที่        | D1 Mini Pro | GPIO |
|----------------|-------------|------|
| MPR121 I2C     | SDA=D2, SCL=D1       | 4, 5 |
| QR Reader      | RX=D6, TX=D5 (ถ้าใช้ SoftwareSerial) | 12, 14 |

ปรับ `#define` ในไฟล์ `.ino` ให้ตรงกับบอร์ดและจอที่ใช้

### ทดสอบจอ 2 ตัว (test_display)

โฟลเดอร์ `test_display/` มีสเก็ตช์ **test_display.ino** สำหรับทดสอบจอ KMR1441_SPI V2 สองตัวเท่านั้น (ไม่มี WiFi/KeyPad/API):

- เปิด `code/hardware/test_display/test_display.ino` ใน Arduino IDE
- เลือก Board: **LOLIN(WEMOS) D1 mini Pro**, พอร์ต COM ที่ใช้
- ไลบรารี: Adafruit ST7735 and ST7789, Adafruit GFX
- อัปโหลดแล้วจอจะวนแสดง: แถบสี + ข้อความ Display 1/2, เต็มจอแดง/เขียว/น้ำเงิน, รูปทรง, ขาว/ดำ (Serial 115200 แสดงสถานะ)

Pinout เหมือน Micro POS: TFT1 CS=D8, TFT2 CS=D4, DC=D3, RST=D0, MOSI=D7, SCK=D5, BL→3.3V  
ถ้าจอไม่ขึ้นภาพ: ในไฟล์เปลี่ยน `#define TFT_USE_ST7789 1` หรือสลับ `TFT_INIT_TAB` เป็น `INITR_GREENTAB` / `INITR_144GREENTAB`

**test_ST7735S** – โฟลเดอร์ `test_ST7735S/` เป็นสเก็ตช์ทดสอบจอ **ST7735S** เฉพาะ (ไม่มี ST7789) สำหรับ ESP8266 จอ 2 ตัว 128x128 พินเดียวกัน ใช้เมื่อต้องการทดสอบเฉพาะ driver ST7735/ST7735S โดยเปลี่ยน `TFT_INIT_TAB` ได้ (INITR_144GREENTAB, INITR_GREENTAB, INITR_BLACKTAB, INITR_18GREENTAB)

### ถ้าจอ SPI ไม่มีภาพเลย / สีขาวทั้งสอง

1. **ต่อ BL (Backlight)** – ขา **BL** ของแต่ละจอต้องต่อ **3.3V** (หรือผ่านตัวต้าน 100–330Ω) ถ้าไม่ต่อจอมืดหรือขาว ไม่มีภาพ
2. **ต่อ MOSI และ SCK** – จอต้องต่อ **D7 (MOSI)** และ **D5 (SCK)** ไปยังบอร์ด ถ้าขาดจอจะไม่ได้รับข้อมูล
3. **ตรวจ CS/DC/RST** – จอ 1: CS=D8, DC=D3, RST=D0 | จอ 2: CS=D4, DC=D3, RST=D0 (DC,RST ใช้ร่วมกันได้)
4. **แรงดัน** – ใช้ **3.3V** ให้จอ ห้ามใช้ 5V
5. **ลอง driver อื่น** – ในไฟล์ .ino ตั้ง `#define TFT_USE_ST7789 1` (ปกติ 0 = ST7735) แล้วอัปโหลดใหม่ – จอ 128x128 บางรุ่นใช้ชิป **ST7789**
6. **ลอง init อื่น (เมื่อใช้ ST7735)** – เปลี่ยน `TFT_INIT_TAB` เป็นอย่างใดอย่างหนึ่งแล้วอัปโหลดใหม่:
   - `INITR_144GREENTAB` (จอ 1.44" – ค่าเริ่มต้นใน test_display)
   - `INITR_GREENTAB`
   - `INITR_BLACKTAB`
7. **ใช้ test_display ก่อน** – เปิด `test_display/test_display.ino` อัปโหลดแล้วเปิด Serial 115200 จะมีข้อความช่วยเช็กและหลัง init จะมีจอแดงสั้นๆ ถ้าเห็นแดง = จอทำงาน

## EEPROM Config

- **ssid, wifi_pass** – WiFi
- **mode** – 0=จำนวนเงินทีละรายการ+Enter, 1=จำนวนเงินสะสม+Enter (กด Enter ค้าง 5 วินาที = ปิดบิล), 2=เมนูทีละรายการ+Enter, 3=เมนูหลายรายการ+Enter (กด Enter ค้าง 5 วินาที = ปิดบิล)
- **machine_id** – รหัสเครื่องไม่ซ้ำ (เช่น MPOS-001) ใช้ใน ref3 / receipt
- **api_host** – URL เซิร์ฟเวอร์ API (เช่น `http://192.168.1.100:8000`)
- **store_id** – **Key หลักกลุ่มอุปกรณ์**: รหัสร้านในระบบ (ใช้เรียก API และ sync กับ Store-POS / จอ signage) Micro POS ที่ตั้ง store_id เดียวกับ Store-POS (เช่น 1) จะแสดง QR และ "ได้รับเงิน" ตาม Store-POS ทันที
- **store_name, tax_id** – ชื่อร้าน, เลขประจำตัวผู้เสียภาษี
- **logo** – (optional) ข้อมูลโลโก้สำหรับแสดง

## การเชื่อมต่อและตรวจสอบอุปกรณ์ (Serial 115200)

เปิด Serial Monitor ที่ **115200 baud** หลัง boot จะเห็น:

- **Hardware / Connection** – สรุป pinout (TFT1, TFT2, MPR121 I2C, QR)
- **Device check** – สถานะ TFT1, TFT2, MPR121 (OK หรือ NOT FOUND พร้อมคำแนะนำตรวจสอบสาย/พูลอัพ)
- **KeyPad debug** – ทุกครั้งที่กดปุ่มจะพิมพ์ลง Serial เช่น `KeyPad: pad 1 -> '7' (digit)` หรือ `(del)` / `(enter)` ปิดได้โดยตั้ง `KEYPAD_DEBUG` เป็น 0 ในไฟล์ .ino
- **Network/API debug** – เมื่อเชื่อม WiFi จะพิมพ์ `Network: <status> SSID=...` ทุก 5 วินาที (status เช่น NO_SSID, FAILED) และเมื่อเชื่อมได้ `Network: connected ...` เมื่อเรียก API health จะพิมพ์ `API: GET ... -> 200 OK` หรือ `-> xxx fail` ปิดได้โดยตั้ง `NETWORK_DEBUG` เป็น 0
- **WiFi timeout** – ถ้าเชื่อม WiFi ไม่ได้ภายใน 20 วินาที จะหยุดลองและแสดง "WiFi timeout" แล้วเข้าโหมด idle ใช้ Serial ส่ง `SET SSID <ชื่อ WiFi>`, `SET PASS <รหัส>`, `SAVE` แล้ว reboot (ปิดเปิดเครื่อง) เปลี่ยน timeout ได้ที่ `WIFI_CONNECT_TIMEOUT_MS` ใน .ino (0 = ไม่ timeout)
- **Sample image** – หลัง boot จะแสดงภาพตัวอย่างบนจอคนขาย (Display 1) และจอคนซื้อ (Display 2) เป็นเวลา 2 วินาที (กรอบขาว, ข้อความ Display 1/2, Seller/Customer, แถบสีน้ำเงิน/เขียว/แดง)

ถ้า MPR121 แสดง "NOT FOUND":
- ตรวจสาย SDA=D2(GPIO4), SCL=D1(GPIO5), 3.3V, GND
- I2C ต้องมี pull-up 2.2k–4.7k บน SDA และ SCL (บางบอร์ดมีในตัว)
- ลองสลับ SDA/SCL หรือใช้ I2C scanner หา address

---

## Serial Config (115200)

เปิด Serial Monitor ที่ 115200 baud แล้วส่งคำสั่ง (จบด้วย Enter):

- `STATUS` – แสดงสถานะ WiFi, API, store_id, machine_id, mode
- `SET SSID <ชื่อเครือข่าย>`
- `SET PASS <รหัสผ่าน WiFi>`
- `SET API <URL>` เช่น `http://192.168.1.100:8000`
- `SET STORE <ตัวเลข>` – store_id
- `SET MACHINE <รหัสเครื่อง>` เช่น MPOS-001
- `SET MODE <0|1|2|3>`
- `SAVE` – บันทึก config ลง EEPROM
- `HELP` – แสดงคำสั่ง

## การ sync กับ Store-POS (store_id = Key กลุ่ม)

- **Key หลักกลุ่ม**: ทุกอุปกรณ์และหน้าต่างที่ใช้ **store_id เดียวกัน** (เช่น 1) จะอยู่ในร้านเดียวกัน
- **Store-POS (เว็บ)** เปิด `/store-pos` หรือ `/launch?store_id=1` → เลือกร้าน store_id=1
- **Micro POS (ฮาร์ดแวร์)** ตั้ง `SET STORE 1` แล้ว `SAVE` → store_id=1
- **Flow แบบ seamless**:
  1. Store-POS กดสร้าง PromptPay QR → API เรียก `POST /api/signage/set-display` (store_id, qr_image, amount)
  2. Micro POS โพล `GET /api/signage/display?store_id=1` ทุก 2 วินาที → ได้ status `waiting_payment` + amount → จอลูกค้าแสดง "PromptPay QR", ยอด, "Scan PromptPay"
  3. ลูกค้าจ่ายเงิน → Webhook เรียก API → `set_signage_paid(store_id)` → status เป็น `paid`
  4. Micro POS โพลได้ status `paid` → จอลูกค้าแสดง "Received xxx.xx THB", "Thank you" ประมาณ 4 วินาที → เรียก `POST /api/signage/ack-paid?store_id=1` แล้วกลับโหมด idle

ดังนั้น Micro POS จะแสดง QR ทุกครั้งที่ Store-POS สั่ง generate QR และแสดง "ได้รับเงิน" ทันทีเมื่อจ่ายเงินแล้ว โดยทำงานสอดประสานกับ Store-POS ผ่าน **store_id** เดียวกัน

---

## โหมดการทำงาน

1. **เปิดเครื่อง** – อ่าน config จาก EEPROM, แสดงบนจอ 1, จอ 2 แสดง Welcome + logo (ถ้ามี)
2. **เชื่อมต่อ WiFi / API** – เช็คเครือข่ายและเรียก API (เช่น health), แสดง IP และสถานะบนจอ 1
3. **โหมดกราฟิก** – แถบบนจอ: battery %, IP, สถานะเชื่อมต่อ, ระดับสัญญาณ (เท่าที่มีข้อมูล) จากนั้นแสดงตามโหมดและรอรับค่าจากคีย์แพด
4. **โหมดเมนู (2/3)** – ดึงรายการเมนูจาก API `GET /api/menus/store/{store_id}` แสดง [เลขเมนู, ชื่อ, ราคา] (ถ้า API มีจำนวนคงเหลือ สามารถซ่อนเมนูที่เหลือ 0 ได้)
5. **ปิดบิล** – ส่ง `POST /api/stores/{store_id}/generate-promptpay-qr` (เหมือน Store-POS สร้าง QR) แสดงรายละเอียดร้าน, ยอดเงิน, QR (หรือข้อความ Scan PromptPay) ที่จอฝั่งลูกค้า แล้ว poll `GET /api/payment-callback/stores/{store_id}/recent-paid` จนได้รายการที่ตรงยอด (และ ref3 ถ้ามี) ถ้าจ่ายแล้ว แสดง "จ่ายเรียบร้อยแล้ว ยอดเงิน ref1 receipt_number" ที่จอลูกค้า และถ้าต่อ printer ก็สั่งพิมพ์ใบเสร็จได้
6. **ยกเลิกรายการ** – ฝั่งคนขายกด **del ค้าง 10 วินาที** เพื่อยกเลิก ส่ง `POST /api/signage/clear?store_id=...` แล้วกลับไปโหมดรอ (ข้อ 3)
7. **เปลี่ยนโหมด** – กด **del + enter ค้าง 10 วินาที** เปิดเมนูโหมด แล้วเลือกด้วยปุ่ม 7=ขึ้น, 5=ลง, 8=ยืนยัน, 0=กลับ

## อัปโหลดเฟิร์มแวร์ (ESP8266 D1 Mini Pro, COM4)

**วิธีที่ 1 – สคริปต์ (ถ้ามี Arduino CLI ใน PATH)**  
จากโฟลเดอร์ `board_qr_propamt_generate`:

```bat
upload.bat
```

**วิธีที่ 2 – คำสั่ง Arduino CLI โดยตรง**

```bash
cd D:\Projects\FoodCourt\code\hardware\board_qr_propamt_generate
arduino-cli compile --fqbn esp8266:esp8266:d1_mini_pro .
arduino-cli upload -p COM4 --fqbn esp8266:esp8266:d1_mini_pro .
```

**วิธีที่ 3 – Arduino IDE**  
1. เปิด `board_qr_propamt_generate.ino`  
2. Tools → Board → ESP8266 Boards → **LOLIN(WEMOS) D1 mini Pro**  
3. Tools → Port → **COM4**  
4. กดปุ่ม Upload (ลูกศร)

---

## ไลบรารี (Arduino IDE)

- **ESP8266** – Board: "LOLIN(WEMOS) D1 mini Pro"
- **Adafruit MPR121**
- **Adafruit ST7735** และ **Adafruit GFX**
- **ArduinoJson** (v6)

## หมายเหตุ

- **machine_id** ควรกำหนดไม่ซ้ำกันต่อเครื่อง (เก็บใน EEPROM) ใช้เป็น ref3 หรือส่วนหนึ่งของเลขใบเสร็จ
- การแสดง QR บนจอลูกค้าปัจจุบันใช้ข้อความ "Scan PromptPay" และยอด/ref1 ถ้า API ส่ง `qr_payload` (สตริง EMV) มาใน response สามารถใช้ไลบรารีสร้าง QR บน ESP แล้ววาดบนจอได้
- เครื่องพิมพ์ Thermal / Cash Drawer ต่อ Serial 9600 ได้ (Option) – ต้องเพิ่มโค้ดส่ง ESC/POS ในขั้นตอน "จ่ายเรียบร้อยแล้ว"
