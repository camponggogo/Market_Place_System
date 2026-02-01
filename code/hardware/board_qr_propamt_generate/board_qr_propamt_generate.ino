/*
 * Market_Place_System - Micro POS Hardware
 * Board: D1 MINI PRO ESP-8266EX
 * - LCD KMR1441_SPI V2 1.44" 128x128 SPI (Seller) - ST7735
 * - LCD KMR1441_SPI V2 1.44" 128x128 SPI (Customer) - ST7735
 * - MPR121 Capacitive KeyPad (I2C)
 * - QR-Reader via Serial (SoftwareSerial)
 * - Config in EEPROM; Serial 115200 for config/status
 * - Optional: Serial 9600 ESC/POS printer, Cash Drawer
 *
 * API: Market_Place_System backend (store_id from config, machine_id unique per device)
 *
 * === ต้องติดตั้งไลบรารี (Arduino IDE) ===
 * Sketch -> Include Library -> Manage Libraries... แล้วค้นหาและติดตั้ง:
 *   - "Adafruit MPR121" (by Adafruit)  <- คีย์แพด capacitive
 *   - "Adafruit ST7735 and ST7789 Library" (by Adafruit)  <- จอ TFT (รองรับทั้ง ST7735 และ ST7789)
 *   - "Adafruit GFX Library" (by Adafruit)
 *   - "ArduinoJson" (by Benoit Blanchon)  <- ใช้ v6
 * Board: LOLIN(WEMOS) D1 mini Pro (ESP8266)
 */

#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <Adafruit_MPR121.h>
#include <Adafruit_GFX.h>
#include <SPI.h>
#include <EEPROM.h>

// ============== PINOUT (D1 Mini Pro) ==============
// ต้องประกาศก่อนเลือก driver เพื่อให้ทั้ง ST7735 และ ST7789 ใช้พินเดียวกันได้
// SPI จอทั้งสองใช้ Hardware SPI: MOSI=D7(GPIO13), SCK=D5(GPIO14)
// จอมีขา BL (Backlight): ต่อ BL -> 3.3V (ถ้าไม่ต่ออาจมืดหรือจอขาว)
// TFT Seller (KMR1441 V2 128x128): CS=D8, DC=D3, RST=D0
#define TFT1_CS   15   // D8 GPIO15
#define TFT1_DC   0    // D3 GPIO0
#define TFT1_RST  16   // D0 GPIO16
// TFT Customer (KMR1441 V2 128x128): CS=D4, DC=D3, RST=D0 (share DC,RST)
#define TFT2_CS   2    // D4 GPIO2 (builtin LED - ถ้าจอสองขาวลองเปลี่ยน CS เป็นขาอื่น)
#define TFT2_DC   0
#define TFT2_RST  16
// MPR121 I2C: SDA=D2(GPIO4), SCL=D1(GPIO5)
#define QR_RX     12   // D6
#define QR_TX     14   // D5

// ============== เลือก Driver จอ ==============
// 0 = ST7735 (KMR1441 ส่วนใหญ่), 1 = ST7789 (จอ 128x128 บางรุ่นใช้ชิปนี้ - ไม่แสดงภาพกับ ST7735 ลองเปลี่ยน)
#define TFT_USE_ST7789  0

#if TFT_USE_ST7789
#include <Adafruit_ST7789.h>
Adafruit_ST7789 tft1 = Adafruit_ST7789(TFT1_CS, TFT1_DC, TFT1_RST);
Adafruit_ST7789 tft2 = Adafruit_ST7789(TFT2_CS, TFT2_DC, TFT2_RST);
#else
#include <Adafruit_ST7735.h>
// ST7735: ถ้าจอขึ้นหน้าลายหรือหน้าขาว ให้สลับ init
// จอลาย/ขาว = ชนิด tab ไม่ตรง ลอง INITR_BLACKTAB, INITR_GREENTAB หรือ INITR_144GREENTAB (1.44")
#define TFT_INIT_TAB  INITR_BLACKTAB   // ไม่ขึ้นภาพลอง INITR_GREENTAB หรือ INITR_144GREENTAB
Adafruit_ST7735 tft1 = Adafruit_ST7735(TFT1_CS, TFT1_DC, TFT1_RST);
Adafruit_ST7735 tft2 = Adafruit_ST7735(TFT2_CS, TFT2_DC, TFT2_RST);
#endif

Adafruit_MPR121 cap = Adafruit_MPR121();

// ============== EEPROM CONFIG LAYOUT ==============
#define EEPROM_SIZE 1024
#define MAGIC 0x4D50  // "MP" Market Place
struct Config {
  uint16_t magic;
  char ssid[32];
  char wifi_pass[64];
  uint8_t mode;           // 0=amount single, 1=amount accum, 2=menu single, 3=menu multi
  char machine_id[24];    // unique per device, e.g. "MPOS-001"
  char api_host[96];      // e.g. "http://192.168.1.100:8000"
  uint16_t store_id;      // store_id for API (same as backend store)
  char store_name[32];
  char tax_id[20];
  uint8_t logo[128];      // small 64x64 or placeholder (optional)
};
#define CONFIG_OFFSET 0
Config cfg;

// ============== KEYPAD MPR121 ==============
// Key index -> character: [0=del, 1=7, 2=4, 3=1, 4=0, 5=8, 6=5, 7=2, 8=enter, 9=9, 10=6, 11=3]
const char KEY_MAP[] = { 'D', '7', '4', '1', '0', '8', '5', '2', 'E', '9', '6', '3' };  // D=del E=enter
uint16_t lastTouched = 0;
unsigned long keyDownTime = 0;
bool keyDelDown = false, keyEnterDown = false;
bool mpr121Ok = false;  // set in setup after cap.begin()

// ============== STATE ==============
enum AppState { BOOT, CONFIG_SCREEN, WIFI_CONNECT, API_POLL, IDLE, ENTER_AMOUNT, ENTER_MENU, ENTER_WAIT_RELEASE, BILL_QR, BILL_PAID, MODE_MENU, MENU_LIST };
AppState state = BOOT;
unsigned long enterHeldStart = 0;  // for Enter long-press 5s = bill (mode 1/3)
String inputBuffer;
float currentAmount = 0;
float billAmount = 0;
String billRef1, billReceiptNo;
unsigned long lastPoll = 0;
unsigned long billStartTime = 0;
int menuIndex = 0;
int menuTotal = 0;
struct MenuItem { int id; String name; float price; bool active; };
MenuItem menuItems[32];
#define menus menuItems
int selectedMenus[32];
int selectedCount = 0;
String lastPaidSince;
int receiptNumber = 0;

// ============== SIGNAGE SYNC (Store-POS = store_id) ==============
// Key หลักกลุ่มอุปกรณ์ = store_id (Micro POS, Store-POS web, จอ signage ใช้ store_id เดียวกัน)
// เมื่อ Store-POS กดสร้าง QR -> API signage set-display -> Micro POS poll display แล้วแสดง QR
// เมื่อจ่ายเงินแล้ว webhook -> API signage paid -> Micro POS แสดง "ได้รับเงิน ยอด xxx.xx แล้ว" ทันที
#define SIGNAGE_POLL_MS 2000
#define SIGNAGE_PAID_SHOW_MS 4000
String signageStatus = "";           // "", "waiting_payment", "paid"
float signageAmount = 0;
unsigned long signagePaidShowUntil = 0;  // มิลลิวินาทีที่ต้อง ack-paid แล้วกลับ idle
unsigned long lastSignagePoll = 0;

// ============== WIFI & API ==============
WiFiClient wifiClient;
HTTPClient http;
String apiBase() { return String(cfg.api_host) + "/api"; }

// ใช้ใน NETWORK_DEBUG; ต้องประกาศนอก #if เพื่อให้ compiler เห็นใน loop()
const char* wifiStatusStr(int s) {
  switch (s) {
    case WL_IDLE_STATUS:      return "IDLE";
    case WL_NO_SSID_AVAIL:    return "NO_SSID (ชื่อ WiFi ผิด?)";
    case WL_SCAN_COMPLETED:   return "SCAN_DONE";
    case WL_CONNECTED:        return "CONNECTED";
    case WL_CONNECT_FAILED:   return "FAILED (รหัสผิด?)";
    case WL_CONNECTION_LOST:  return "LOST";
    case WL_DISCONNECTED:     return "DISCONNECTED";
    default:                  return "?";
  }
}

// ============== EEPROM ==============
void configLoad() {
  EEPROM.begin(EEPROM_SIZE);
  EEPROM.get(CONFIG_OFFSET, cfg);
  if (cfg.magic != MAGIC) {
    cfg.magic = MAGIC;
    strncpy(cfg.ssid, "Link 2.4GHz", sizeof(cfg.ssid)-1);
    strncpy(cfg.wifi_pass, "P@ssw0rdGem8L!nk", sizeof(cfg.wifi_pass)-1);
    cfg.mode = 0;
    strncpy(cfg.machine_id, "MPOS-001", sizeof(cfg.machine_id)-1);
    strncpy(cfg.api_host, "http://192.168.1.138:8000", sizeof(cfg.api_host)-1);
    cfg.store_id = 1;
    strncpy(cfg.store_name, "Micro POS", sizeof(cfg.store_name)-1);
    strncpy(cfg.tax_id, "", sizeof(cfg.tax_id)-1);
    configSave();
  }
}
void configSave() {
  EEPROM.put(CONFIG_OFFSET, cfg);
  EEPROM.commit();
}

// ============== DISPLAY HELPERS ==============
void tft1Header(const char* status) {
  tft1.fillRect(0, 0, 128, 12, ST77XX_BLUE);
  tft1.setTextColor(ST77XX_WHITE);
  tft1.setCursor(2, 2);
  tft1.print(WiFi.RSSI());
  tft1.print(" ");
  tft1.print(status);
}
// Boot: Seller screen = icon + "Seller" (KMR1441 128x128)
void drawBootSeller() {
  tft1.fillScreen(ST77XX_BLACK);
  tft1.setTextColor(ST77XX_WHITE);
  // Icon: simple store (rectangle + triangle roof) - center 64 for 128 width
  int cx = 64, top = 8, w = 48, h = 32;
  tft1.fillRoundRect(cx - w/2, top + 6, w, h, 4, ST77XX_BLUE);
  tft1.fillTriangle(cx - w/2, top + 6, cx, top, cx + w/2, top + 6, ST77XX_CYAN);
  tft1.setCursor(cx - 18, top + h + 12);
  tft1.setTextSize(2);
  tft1.print("Seller");
  tft1.setTextSize(1);
}

// Boot: Customer screen = icon + "Customer"
void drawBootCustomer() {
  tft2.fillScreen(ST77XX_BLACK);
  tft2.setTextColor(ST77XX_WHITE);
  // Icon: simple person (head + body)
  int cx = 64, cy = 38;
  tft2.fillCircle(cx, cy - 12, 14, ST77XX_BLUE);
  tft2.fillRoundRect(cx - 10, cy + 4, 20, 28, 4, ST77XX_CYAN);
  tft2.setCursor(cx - 32, cy + 38);
  tft2.setTextSize(2);
  tft2.print("Customer");
  tft2.setTextSize(1);
}

// Sample image: Display 1 (Seller) - KMR1441 128x128
void drawSampleDisplay1() {
  tft1.fillScreen(ST77XX_BLACK);
  tft1.drawRect(0, 0, 128, 128, ST77XX_WHITE);
  tft1.setTextColor(ST77XX_WHITE);
  tft1.setCursor(24, 4);
  tft1.setTextSize(2);
  tft1.print("Display 1");
  tft1.setCursor(40, 24);
  tft1.setTextSize(1);
  tft1.print("Seller");
  tft1.setTextSize(1);
  // Sample graphic: 3 horizontal color bars
  tft1.fillRect(10, 38, 108, 18, ST77XX_BLUE);
  tft1.fillRect(10, 58, 108, 18, ST77XX_GREEN);
  tft1.fillRect(10, 78, 108, 18, ST77XX_RED);
  tft1.setCursor(10, 102);
  tft1.print("Sample image");
}

// Sample image: Display 2 (Customer) - color bars + label
void drawSampleDisplay2() {
  tft2.fillScreen(ST77XX_BLACK);
  tft2.drawRect(0, 0, 128, 128, ST77XX_WHITE);
  tft2.setTextColor(ST77XX_WHITE);
  tft2.setCursor(24, 4);
  tft2.setTextSize(2);
  tft2.print("Display 2");
  tft2.setCursor(40, 24);
  tft2.setTextSize(1);
  tft2.print("Customer");
  tft2.setTextSize(1);
  // Sample graphic: 3 horizontal color bars
  tft2.fillRect(10, 38, 108, 18, ST77XX_BLUE);
  tft2.fillRect(10, 58, 108, 18, ST77XX_GREEN);
  tft2.fillRect(10, 78, 108, 18, ST77XX_RED);
  tft2.setCursor(10, 102);
  tft2.print("Sample image");
}

// ============== API CALLS ==============
bool apiGetHealth() {
  String url = String(cfg.api_host) + "/health";
  http.begin(wifiClient, url);
  int code = http.GET();
#if NETWORK_DEBUG
  Serial.print(F("API: GET "));
  Serial.print(url);
  Serial.print(F(" -> "));
  Serial.print(code);
  Serial.println(code == 200 ? F(" OK") : F(" fail"));
#endif
  http.end();
  return (code == 200);
}
bool apiGetMenus() {
  String url = apiBase() + "/menus/store/" + String(cfg.store_id);
  http.begin(wifiClient, url);
  int code = http.GET();
  if (code != 200) { http.end(); return false; }
  String body = http.getString();
  http.end();
  DynamicJsonDocument doc(2048);
  if (deserializeJson(doc, body) != DeserializationError::Ok) return false;
  JsonArray arr = doc.as<JsonArray>();
  menuTotal = 0;
  for (JsonObject o : arr) {
    if (menuTotal >= 32) break;
    if (!o["is_active"].as<bool>()) continue;
    menus[menuTotal].id = o["id"].as<int>();
    menus[menuTotal].name = o["name"].as<String>();
    menus[menuTotal].price = o["unit_price"].as<float>();
    menus[menuTotal].active = true;
    menuTotal++;
  }
  return true;
}
bool apiCreateQR(float amount, int menuId, String ref3, String& outRef1, String& outQrBase64) {
  String url = apiBase() + "/stores/" + String(cfg.store_id) + "/generate-promptpay-qr";
  http.begin(wifiClient, url);
  http.addHeader("Content-Type", "application/json");
  DynamicJsonDocument req(256);
  req["amount"] = amount;
  if (menuId > 0) req["menu_id"] = menuId;
  if (ref3.length()) req["ref3"] = ref3;
  String body;
  serializeJson(req, body);
  int code = http.POST(body);
  if (code != 200) { http.end(); return false; }
  String res = http.getString();
  http.end();
  DynamicJsonDocument doc(1536);
  if (deserializeJson(doc, res) != DeserializationError::Ok) return false;
  outRef1 = doc["ref1"].as<String>();
  outQrBase64 = doc["qr_code_tag30"].as<String>();
  if (outQrBase64.startsWith("data:image")) {
    int i = outQrBase64.indexOf("base64,");
    if (i >= 0) outQrBase64 = outQrBase64.substring(i + 7);
  }
  return true;
}
// recent-paid items: id, amount, paid_at, ref2, ref3 (no ref1 in list)
bool apiRecentPaid(String since, float amount, String ref3Match, String& paidAt) {
  String url = apiBase() + "/payment-callback/stores/" + String(cfg.store_id) + "/recent-paid?limit=20";
  if (since.length()) url += "&since=" + since;
  http.begin(wifiClient, url);
  int code = http.GET();
  if (code != 200) { http.end(); return false; }
  String body = http.getString();
  http.end();
  DynamicJsonDocument doc(1024);
  if (deserializeJson(doc, body) != DeserializationError::Ok) return false;
  JsonArray arr = doc["items"].as<JsonArray>();
  for (JsonObject o : arr) {
    float a = o["amount"].as<float>();
    if (fabs(a - amount) < 0.01f) {
      if (ref3Match.length() && o["ref3"].as<String>() != ref3Match) continue;
      paidAt = o["paid_at"].as<String>();
      return true;
    }
  }
  return false;
}
void apiSignageClear() {
  String url = String(cfg.api_host) + "/api/signage/clear?store_id=" + String(cfg.store_id);
  http.begin(wifiClient, url);
  http.POST("");
  http.end();
}

// ดึงสถานะ signage ของร้าน (Store-POS สร้าง QR -> set-display; จ่ายแล้ว -> paid)
bool apiSignageGetDisplay() {
  String url = String(cfg.api_host) + "/api/signage/display?store_id=" + String(cfg.store_id);
  http.begin(wifiClient, url);
  int code = http.GET();
  if (code != 200) { http.end(); return false; }
  String body = http.getString();
  http.end();
  DynamicJsonDocument doc(512);
  if (deserializeJson(doc, body) != DeserializationError::Ok) return false;
  const char* s = doc["status"].as<const char*>();
  signageStatus = s ? String(s) : "";
  signageAmount = doc["amount"].as<float>();
  return true;
}

void apiSignageAckPaid() {
  String url = String(cfg.api_host) + "/api/signage/ack-paid?store_id=" + String(cfg.store_id);
  http.begin(wifiClient, url);
  http.POST("");
  http.end();
}

// ============== KEYPAD ==============
// Debug: set 1 to print key presses to Serial (115200)
#define KEYPAD_DEBUG 1
// Debug: set 1 to print network and API connect to Serial
#define NETWORK_DEBUG 1
// WiFi: timeout หลังกี่ ms ถ้าเชื่อมไม่สำเร็จ (0 = ไม่ timeout)
#define WIFI_CONNECT_TIMEOUT_MS 20000

char readKey() {
  if (!mpr121Ok) return 0;
  uint16_t cur = cap.touched();
  for (int i = 0; i < 12; i++) {
    if (cur & (1 << i) && !(lastTouched & (1 << i))) {
      lastTouched = cur;
      char k = KEY_MAP[i];
#if KEYPAD_DEBUG
      Serial.print(F("KeyPad: pad "));
      Serial.print(i);
      Serial.print(F(" -> '"));
      Serial.print(k);
      Serial.print(F("' "));
      if (k == 'D') Serial.println(F("(del)"));
      else if (k == 'E') Serial.println(F("(enter)"));
      else Serial.println(F("(digit)"));
#endif
      return k;
    }
  }
  lastTouched = cur;
  return 0;
}
void updateLongPress() {
  if (!mpr121Ok) { keyDelDown = false; keyEnterDown = false; return; }
  uint16_t cur = cap.touched();
  keyDelDown = (cur & 1) != 0;
  keyEnterDown = (cur & (1 << 8)) != 0;
}

// ============== MODE MENU (long press del+enter >10s) ==============
int modeMenuSelection = 0;
const char* MODE_STR[] = { "Amount x1+Enter", "Amount Sum+Enter", "Menu x1+Enter", "Menu Multi+Enter" };
void drawModeMenu() {
  tft1.fillScreen(ST77XX_BLACK);
  tft1.setTextColor(ST77XX_WHITE);
  tft1.setCursor(0, 0);
  tft1.print("MODE: 7Up 5Dn 8Ok 0Back");
  for (int i = 0; i < 4; i++) {
    tft1.setCursor(2, 14 + i * 10);
    if (i == modeMenuSelection) tft1.print(">");
    tft1.print(MODE_STR[i]);
  }
}
void runModeMenu(char k) {
  if (k == '8') { cfg.mode = modeMenuSelection; configSave(); state = IDLE; return; }
  if (k == '0') { state = IDLE; return; }
  if (k == '7') { modeMenuSelection = (modeMenuSelection - 1 + 4) % 4; drawModeMenu(); }
  if (k == '5') { modeMenuSelection = (modeMenuSelection + 1) % 4; drawModeMenu(); }
}

// ============== IDLE / ENTER AMOUNT ==============
void drawIdleSeller() {
  tft1.fillScreen(ST77XX_BLACK);
  tft1Header(WiFi.localIP().toString().c_str());
  tft1.setTextColor(ST77XX_WHITE);
  tft1.setCursor(0, 14);
  tft1.print("Store ");
  tft1.println(cfg.store_id);
  tft1.print("Mode:");
  tft1.println(MODE_STR[cfg.mode]);
  tft1.print("Amt:");
  tft1.println(inputBuffer);
  tft1.print("Total:");
  tft1.println(currentAmount);
}
void drawIdleCustomer() {
  tft2.fillScreen(ST77XX_BLACK);
  tft2.setTextColor(ST77XX_WHITE);
  tft2.setCursor(10, 40);
  tft2.setTextSize(2);
  tft2.print("PromptPay");
  tft2.setTextSize(1);
  tft2.setCursor(10, 70);
  tft2.print("Ready - Scan when bill");
}

// จอลูกค้า: แสดง QR จาก Store-POS (sync กับ store_id)
void drawSignageQR(float amount) {
  tft2.fillScreen(ST77XX_BLACK);
  tft2.setTextColor(ST77XX_WHITE);
  tft2.setCursor(0, 0);
  tft2.setTextSize(2);
  tft2.print("PromptPay QR");
  tft2.setTextSize(1);
  tft2.setCursor(0, 16);
  tft2.print(cfg.store_name);
  tft2.setCursor(0, 26);
  tft2.print("Store ");
  tft2.println(cfg.store_id);
  tft2.print("Amount: ");
  tft2.println(amount, 2);
  tft2.setCursor(0, 56);
  tft2.setTextSize(2);
  tft2.print("Scan PromptPay");
  tft2.setTextSize(1);
}

// จอลูกค้า: ได้รับเงินแล้ว (หลัง webhook set_signage_paid) - seamless กับ Store-POS
void drawSignagePaid(float amount) {
  tft2.fillScreen(ST77XX_GREEN);
  tft2.setTextColor(ST77XX_BLACK);
  tft2.setCursor(5, 20);
  tft2.setTextSize(1);
  tft2.print("Received ");
  tft2.print(amount, 2);
  tft2.println(" THB");
  tft2.setCursor(5, 38);
  tft2.setTextSize(2);
  tft2.print("Thank you");
  tft2.setTextSize(1);
  tft2.setCursor(5, 65);
  tft2.print("Received!");
}

// ============== MENU LIST (mode 2/3) ==============
void drawMenuList() {
  tft1.fillScreen(ST77XX_BLACK);
  tft1Header("Menu 7Up 5Dn 8Add 0Back");
  tft1.setTextColor(ST77XX_WHITE);
  for (int i = 0; i < 6 && (menuIndex + i) < menuTotal; i++) {
    int idx = menuIndex + i;
    tft1.setCursor(0, 14 + i * 10);
    if (idx == menuIndex) tft1.print(">");
    tft1.print(menus[idx].name);
    tft1.print(" ");
    tft1.println(menus[idx].price);
  }
}
void runMenuList(char k) {
  if (k == '0') { state = IDLE; drawIdleSeller(); drawIdleCustomer(); return; }
  if (k == '8') {
    if (menuIndex < menuTotal && menus[menuIndex].active) {
      currentAmount += menus[menuIndex].price;
      inputBuffer = "";
    }
    drawIdleSeller();
    return;
  }
  if (k == '7') { if (menuIndex > 0) menuIndex--; drawMenuList(); }
  if (k == '5') { if (menuIndex < menuTotal - 1) menuIndex++; drawMenuList(); }
}

// ============== BILL QR (show QR on customer screen, poll paid) ==============
void drawBillCustomer(String ref1, float amount, String receiptNo) {
  tft2.fillScreen(ST77XX_BLACK);
  tft2.setTextColor(ST77XX_WHITE);
  tft2.setCursor(0, 0);
  tft2.setTextSize(2);
  tft2.print("PromptPay QR");
  tft2.setTextSize(1);
  tft2.setCursor(0, 16);
  tft2.print(cfg.store_name);
  tft2.setCursor(0, 26);
  tft2.print("Amount: ");
  tft2.println(amount);
  tft2.print("Ref: ");
  tft2.println(ref1);
  tft2.print("Receipt: ");
  tft2.println(receiptNo);
  tft2.setCursor(0, 56);
  tft2.setTextSize(2);
  tft2.print("Scan PromptPay");
  tft2.setTextSize(1);
  // If we had qr_payload we would draw QR here with a small QR lib
}
void drawBillPaid(float amount, String ref1, String receiptNo) {
  tft2.fillScreen(ST77XX_GREEN);
  tft2.setTextColor(ST77XX_BLACK);
  tft2.setCursor(5, 40);
  tft2.setTextSize(2);
  tft2.print("Paid OK");
  tft2.setTextSize(1);
  tft2.setCursor(5, 70);
  tft2.print("Amount: ");
  tft2.println(amount);
  tft2.print("Ref: ");
  tft2.println(ref1);
  tft2.print("Receipt: ");
  tft2.println(receiptNo);
}

// ============== SERIAL CONFIG (115200) ==============
#define SERIAL_CMD_MAX 128
char serialBuf[SERIAL_CMD_MAX];
uint8_t serialLen = 0;
void processSerialConfig() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      serialBuf[serialLen] = '\0';
      if (serialLen == 0) break;
      String cmd = String(serialBuf);
      cmd.trim();
      serialLen = 0;
      if (cmd == "STATUS") {
        Serial.println("--- STATUS ---");
        Serial.print("WiFi: ");
        if (WiFi.status() == WL_CONNECTED) Serial.println(WiFi.localIP()); else Serial.println("Disconnected");
        Serial.print("RSSI: "); Serial.println(WiFi.RSSI());
        Serial.print("API: "); Serial.println(cfg.api_host);
        Serial.print("store_id: "); Serial.println(cfg.store_id);
        Serial.print("machine_id: "); Serial.println(cfg.machine_id);
        Serial.print("mode: "); Serial.println(cfg.mode);
      } else if (cmd.startsWith("SET SSID ")) {
        cmd.substring(9).toCharArray(cfg.ssid, sizeof(cfg.ssid));
        Serial.println("SSID set");
      } else if (cmd.startsWith("SET PASS ")) {
        cmd.substring(9).toCharArray(cfg.wifi_pass, sizeof(cfg.wifi_pass));
        Serial.println("PASS set");
      } else if (cmd.startsWith("SET API ")) {
        cmd.substring(8).toCharArray(cfg.api_host, sizeof(cfg.api_host));
        Serial.println("API set");
      } else if (cmd.startsWith("SET STORE ")) {
        cfg.store_id = cmd.substring(10).toInt();
        Serial.println("store_id set");
      } else if (cmd.startsWith("SET MACHINE ")) {
        cmd.substring(12).toCharArray(cfg.machine_id, sizeof(cfg.machine_id));
        Serial.println("machine_id set");
      } else if (cmd.startsWith("SET MODE ")) {
        cfg.mode = cmd.substring(9).toInt() % 4;
        Serial.println("mode set");
      } else if (cmd == "SAVE") {
        configSave();
        Serial.println("Config saved");
      } else if (cmd == "HELP") {
        Serial.println("STATUS, SET SSID x, SET PASS x, SET API x, SET STORE n, SET MACHINE x, SET MODE n, SAVE, HELP");
      }
      serialLen = 0;
      break;
    } else if (serialLen < SERIAL_CMD_MAX - 1) serialBuf[serialLen++] = c;
  }
}

// Enter long-press 5s = bill (mode 1/3): when Enter released after >5s, do bill
void checkEnterRelease() {
  if (enterHeldStart == 0 || !mpr121Ok) return;
  uint16_t cur = cap.touched();
  if (cur & (1 << 8)) return;  // still held
  unsigned long held = millis() - enterHeldStart;
  enterHeldStart = 0;
  if (held >= 5000 && (cfg.mode == 1 || cfg.mode == 3)) {
    if (currentAmount > 0) {
      billAmount = currentAmount;
      billRef1 = "";
      String qrB64;
      receiptNumber++;
      String ref3 = String(cfg.machine_id) + "-" + String(receiptNumber);
      if (apiCreateQR(billAmount, 0, ref3, billRef1, qrB64)) {
        billReceiptNo = ref3;
        billStartTime = millis();
        lastPaidSince = "";
        state = BILL_QR;
        drawBillCustomer(billRef1, billAmount, billReceiptNo);
      }
    }
  } else if (cfg.mode == 1 || cfg.mode == 3) {
    currentAmount += inputBuffer.toFloat() / 100.0f;
    inputBuffer = "";
  }
}

// ============== HARDWARE CHECK (Serial) ==============
void printHardwareConnection() {
  Serial.println(F("\n=== Hardware / Connection ==="));
  Serial.println(F("Pinout (D1 Mini Pro):"));
  Serial.println(F("  TFT1 (Seller):  CS=D8, DC=D3, RST=D0 [128x128]"));
  Serial.println(F("  TFT2 (Customer): CS=D4, DC=D3, RST=D0 [128x128]"));
#if TFT_USE_ST7789
  Serial.println(F("  Driver: ST7789"));
#else
  Serial.println(F("  Driver: ST7735"));
#endif
  Serial.println(F("  MPR121 (I2C):   SDA=D2(GPIO4), SCL=D1(GPIO5), addr=0x5A"));
  Serial.println(F("  QR Reader:      RX=D6(GPIO12), TX=D5(GPIO14) [optional]"));
  Serial.println();
}

void printDeviceStatus() {
  Serial.println(F("=== Device check ==="));
  // TFT1 (128x128)
  Serial.print(F("  TFT1 (Seller):   "));
#if TFT_USE_ST7789
  tft1.init(128, 128);
#else
  tft1.initR(TFT_INIT_TAB);
#endif
  tft1.fillScreen(ST77XX_BLACK);
  Serial.println(F("OK"));
  // TFT2 (128x128)
  Serial.print(F("  TFT2 (Customer): "));
#if TFT_USE_ST7789
  tft2.init(128, 128);
#else
  tft2.initR(TFT_INIT_TAB);
#endif
  tft2.fillScreen(ST77XX_BLACK);
  Serial.println(F("OK"));
  // MPR121
  Serial.print(F("  MPR121 (KeyPad): "));
  Wire.begin(4, 5);  // SDA=D2(GPIO4), SCL=D1(GPIO5)
  mpr121Ok = cap.begin(0x5A);
  if (mpr121Ok) {
    Serial.println(F("OK (I2C 0x5A)"));
  } else {
    Serial.println(F("NOT FOUND"));
    Serial.println(F("    -> Check: SDA=D2, SCL=D1, 3.3V, GND, I2C pull-up 2.2k-4.7k on SDA/SCL"));
    Serial.println(F("    -> Try: swap SDA/SCL, or use I2C scanner to find address"));
  }
  Serial.println();
}

// ============== SETUP ==============
void setup() {
  Serial.begin(115200);
  Serial.println(F("\nMicro POS Market_Place_System"));
  configLoad();

  printHardwareConnection();
  printDeviceStatus();

  tft1.setRotation(1);
  tft2.setRotation(1);
  tft1.setTextSize(1);
  tft2.setTextSize(1);
  // Boot: Seller = icon + "Seller", Customer = icon + "Customer"
  drawBootSeller();
  drawBootCustomer();
  delay(1500);
  // Sample image on both displays
#if NETWORK_DEBUG
  Serial.println(F("Display: sample image on Display 1 (Seller) and Display 2 (Customer)"));
#endif
  drawSampleDisplay1();
  drawSampleDisplay2();
  delay(2000);
  WiFi.mode(WIFI_STA);
  WiFi.begin(cfg.ssid, cfg.wifi_pass);
  state = WIFI_CONNECT;
  inputBuffer.reserve(32);
  lastPaidSince.reserve(32);
}

// ============== LOOP ==============
void loop() {
  char k = readKey();
  updateLongPress();
  static unsigned long longPressCheck = 0;
  if (millis() - longPressCheck > 500) {
    longPressCheck = millis();
    if (keyDelDown && keyEnterDown && state != MODE_MENU) {
      static unsigned long comboStart = 0;
      if (comboStart == 0) comboStart = millis();
      else if (millis() - comboStart > 10000) {
        state = MODE_MENU;
        modeMenuSelection = cfg.mode;
        drawModeMenu();
        comboStart = 0;
      }
    } else if (state == BILL_QR && keyDelDown && (millis() - billStartTime > 10000)) {
      apiSignageClear();
      state = IDLE;
      inputBuffer = "";
      currentAmount = 0;
      drawIdleSeller();
      drawIdleCustomer();
    }
  }
  if (!keyDelDown && !keyEnterDown) keyDownTime = 0;

  processSerialConfig();

  switch (state) {
    case WIFI_CONNECT: {
      static bool wifiDebugDone = false;
      static unsigned long wifiConnectStart = 0;
      if (wifiConnectStart == 0) wifiConnectStart = millis();

      if (WiFi.status() == WL_CONNECTED) {
#if NETWORK_DEBUG
        if (!wifiDebugDone) {
          Serial.print(F("Network: connected SSID="));
          Serial.print(cfg.ssid);
          Serial.print(F(" IP="));
          Serial.println(WiFi.localIP());
          Serial.print(F("Network: RSSI "));
          Serial.println(WiFi.RSSI());
          wifiDebugDone = true;
        }
#endif
        tft1.fillScreen(ST77XX_BLACK);
        tft1.setCursor(0, 0);
        tft1.print("WiFi OK ");
        tft1.println(WiFi.localIP());
        state = API_POLL;
      } else {
#if WIFI_CONNECT_TIMEOUT_MS > 0
        if ((unsigned long)(millis() - wifiConnectStart) >= WIFI_CONNECT_TIMEOUT_MS) {
#if NETWORK_DEBUG
          Serial.print(F("Network: timeout after "));
          Serial.print(WIFI_CONNECT_TIMEOUT_MS / 1000);
          Serial.print(F("s status="));
          Serial.println(wifiStatusStr(WiFi.status()));
          Serial.println(F("  -> ใช้ Serial ส่ง SET SSID / SET PASS / SAVE แล้ว reboot"));
#endif
          tft1.fillScreen(ST77XX_BLACK);
          tft1.setCursor(0, 0);
          tft1.println("WiFi timeout");
          tft1.println("Serial: SET SSID/PASS");
          tft1.println("SAVE + reboot");
          state = IDLE;
          drawIdleSeller();
          drawIdleCustomer();
          break;
        }
#endif
#if NETWORK_DEBUG
        static unsigned long lastWifiLog = 0;
        if (millis() - lastWifiLog >= 5000) {
          lastWifiLog = millis();
          Serial.print(F("Network: "));
          Serial.print(wifiStatusStr(WiFi.status()));
          Serial.print(F(" SSID="));
          Serial.println(cfg.ssid);
        }
#endif
        tft1.setCursor(0, 30);
        tft1.print("Connecting...");
      }
      break;
    }

    case API_POLL:
      if (apiGetHealth()) {
        state = IDLE;
        drawIdleSeller();
        drawIdleCustomer();
      } else {
        tft1.setCursor(0, 20);
        tft1.print("API fail");
      }
      break;

    case MODE_MENU:
      if (k) runModeMenu(k);
      break;

    case ENTER_WAIT_RELEASE:
      checkEnterRelease();
      if (enterHeldStart == 0) state = IDLE;
      drawIdleSeller();
      break;

    case MENU_LIST:
      if (k) runMenuList(k);
      break;

    case IDLE: {
      // Signage sync: หลังแสดง "ได้รับเงิน" ครบเวลา -> ack-paid แล้วกลับ idle
      if (signagePaidShowUntil > 0 && (unsigned long)millis() >= signagePaidShowUntil) {
        apiSignageAckPaid();
        signagePaidShowUntil = 0;
        signageStatus = "";
        drawIdleCustomer();
      }
      // Signage sync: poll display ตาม store_id (Store-POS สร้าง QR -> แสดง; จ่ายแล้ว -> แสดง "ได้รับเงิน")
      else if (WiFi.status() == WL_CONNECTED && (unsigned long)(millis() - lastSignagePoll) >= SIGNAGE_POLL_MS) {
        lastSignagePoll = millis();
        if (apiSignageGetDisplay()) {
          if (signageStatus == "paid") {
            drawSignagePaid(signageAmount);
            signagePaidShowUntil = millis() + SIGNAGE_PAID_SHOW_MS;
          } else if (signageStatus == "waiting_payment") {
            drawSignageQR(signageAmount);
          } else if (signageStatus.length() == 0) {
            drawIdleCustomer();
          }
        }
      }

      if (k == '8' && (cfg.mode == 2 || cfg.mode == 3)) {
        if (apiGetMenus()) {
          menuIndex = 0;
          state = MENU_LIST;
          drawMenuList();
        }
        break;
      }
      checkEnterRelease();
      if (k == 'E') {
        if (currentAmount <= 0 && inputBuffer.length() == 0) break;
        if (cfg.mode == 1 || cfg.mode == 3) {
          enterHeldStart = millis();
          state = ENTER_WAIT_RELEASE;
          break;
        }
        billAmount = currentAmount;
        billRef1 = "";
        String qrB64;
        receiptNumber++;
        String ref3 = String(cfg.machine_id) + "-" + String(receiptNumber);
        if (apiCreateQR(billAmount, 0, ref3, billRef1, qrB64)) {
          billReceiptNo = ref3;
          billStartTime = millis();
          lastPaidSince = "";
          state = BILL_QR;
          drawBillCustomer(billRef1, billAmount, billReceiptNo);
          drawIdleSeller();
        }
      } else if (k == 'D') inputBuffer = "", currentAmount = 0;
      else if (k >= '0' && k <= '9') {
        inputBuffer += k;
        if (cfg.mode == 0 || cfg.mode == 2) currentAmount = inputBuffer.toFloat() / 100.0f;
        else currentAmount = inputBuffer.toFloat() / 100.0f;  // accum: same buffer, E adds then clear
        if (inputBuffer.length() > 8) inputBuffer.remove(8);
      }
      drawIdleSeller();
      break;
    }

    case BILL_QR:
      if (millis() - lastPoll > 2000) {
        lastPoll = millis();
        String paidAt;
        if (apiRecentPaid(lastPaidSince, billAmount, billReceiptNo, paidAt)) {
          state = BILL_PAID;
          drawBillPaid(billAmount, billRef1, billReceiptNo);
          // TODO: trigger thermal printer if connected
        }
        if (paidAt.length()) lastPaidSince = paidAt;
      }
      break;

    case BILL_PAID:
      delay(3000);
      state = IDLE;
      inputBuffer = "";
      currentAmount = 0;
      drawIdleSeller();
      drawIdleCustomer();
      break;
  }
  delay(50);
}
