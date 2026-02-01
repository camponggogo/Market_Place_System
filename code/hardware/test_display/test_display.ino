/*
 * test_display.ino - ทดสอบจอ 2 ตัว KMR1441_SPI V2 1.44" 128x128
 * Board: D1 MINI PRO (ESP-8266EX)
 *
 * ใช้เฉพาะจอ TFT ไม่มี WiFi/KeyPad/API
 * Pinout เหมือน Micro POS: TFT1 CS=D8, DC=D3, RST=D0 | TFT2 CS=D4, DC=D3, RST=D0
 * SPI: MOSI=D7, SCK=D5 | BL แต่ละจอ -> 3.3V
 *
 * ไลบรารี: Adafruit ST7735 and ST7789, Adafruit GFX, SPI
 * Board: LOLIN(WEMOS) D1 mini Pro (ESP8266)
 */

#include <Adafruit_GFX.h>
#include <SPI.h>

// ============== PINOUT (D1 Mini Pro) ==============
#define TFT1_CS   15   // D8
#define TFT1_DC   0    // D3
#define TFT1_RST  16   // D0
#define TFT2_CS   2    // D4
#define TFT2_DC   0
#define TFT2_RST  16

// ============== Driver ==============
// 0 = ST7735, 1 = ST7789 (ถ้าไม่มีภาพเลยลองสลับ)
#define TFT_USE_ST7789  0

#if TFT_USE_ST7789
#include <Adafruit_ST7789.h>
Adafruit_ST7789 tft1 = Adafruit_ST7789(TFT1_CS, TFT1_DC, TFT1_RST);
Adafruit_ST7789 tft2 = Adafruit_ST7789(TFT2_CS, TFT2_DC, TFT2_RST);
#else
#include <Adafruit_ST7735.h>
// จอ 1.44" 128x128: ลองตามลำดับ INITR_144GREENTAB -> INITR_GREENTAB -> INITR_BLACKTAB
#define TFT_INIT_TAB  INITR_BLACKTAB
Adafruit_ST7735 tft1 = Adafruit_ST7735(TFT1_CS, TFT1_DC, TFT1_RST);
Adafruit_ST7735 tft2 = Adafruit_ST7735(TFT2_CS, TFT2_DC, TFT2_RST);
#endif

#define TEST_DELAY_MS  2500
// ถ้าจอมีแต่สีผิด/กลับกัน ลองเปิด: 1 = invert
#define TFT_INVERT_DISPLAY  0

// รีเซ็ตฮาร์ดแวร์จอ (TFT1 กับ TFT2 ใช้ RST เดียวกัน = D0)
void hardwareResetDisplays() {
  pinMode(TFT1_RST, OUTPUT);
  digitalWrite(TFT1_RST, LOW);
  delay(50);
  digitalWrite(TFT1_RST, HIGH);
  delay(150);
}

void initDisplays() {
#if TFT_USE_ST7789
  tft1.init(128, 128);
  tft2.init(128, 128);
#else
  tft1.initR(TFT_INIT_TAB);
  tft2.initR(TFT_INIT_TAB);
#endif
  tft1.setRotation(1);
  tft2.setRotation(1);
#if TFT_INVERT_DISPLAY
  tft1.invertDisplay(true);
  tft2.invertDisplay(true);
#endif
  tft1.setTextSize(1);
  tft2.setTextSize(1);
}

// แสดงเต็มจอสีเดียว + ข้อความ
void screenSolid(uint16_t color, const char* label1, const char* label2) {
  tft1.fillScreen(color);
  tft2.fillScreen(color);
  tft1.setTextColor(ST77XX_WHITE);
  tft2.setTextColor(ST77XX_WHITE);
  if (color == ST77XX_WHITE || color == ST77XX_YELLOW || color == ST77XX_CYAN) {
    tft1.setTextColor(ST77XX_BLACK);
    tft2.setTextColor(ST77XX_BLACK);
  }
  tft1.setCursor(20, 56);
  tft1.setTextSize(2);
  tft1.print(label1);
  tft2.setCursor(20, 56);
  tft2.setTextSize(2);
  tft2.print(label2);
}

// แถบสี + Display 1 / Display 2
void screenBars() {
  tft1.fillScreen(ST77XX_BLACK);
  tft1.drawRect(0, 0, 128, 128, ST77XX_WHITE);
  tft1.setTextColor(ST77XX_WHITE);
  tft1.setCursor(24, 4);
  tft1.setTextSize(2);
  tft1.print("Display 1");
  tft1.setCursor(44, 24);
  tft1.setTextSize(1);
  tft1.print("KMR1441");
  tft1.fillRect(10, 38, 108, 18, ST77XX_BLUE);
  tft1.fillRect(10, 58, 108, 18, ST77XX_GREEN);
  tft1.fillRect(10, 78, 108, 18, ST77XX_RED);
  tft1.setCursor(10, 102);
  tft1.print("128x128 SPI V2");

  tft2.fillScreen(ST77XX_BLACK);
  tft2.drawRect(0, 0, 128, 128, ST77XX_WHITE);
  tft2.setTextColor(ST77XX_WHITE);
  tft2.setCursor(24, 4);
  tft2.setTextSize(2);
  tft2.print("Display 2");
  tft2.setCursor(44, 24);
  tft2.setTextSize(1);
  tft2.print("KMR1441");
  tft2.fillRect(10, 38, 108, 18, ST77XX_BLUE);
  tft2.fillRect(10, 58, 108, 18, ST77XX_GREEN);
  tft2.fillRect(10, 78, 108, 18, ST77XX_RED);
  tft2.setCursor(10, 102);
  tft2.print("128x128 SPI V2");
}

// กล่อง + วงกลม
void screenShapes() {
  tft1.fillScreen(ST77XX_BLACK);
  tft2.fillScreen(ST77XX_BLACK);
  tft1.fillRoundRect(14, 14, 100, 100, 8, ST77XX_BLUE);
  tft1.fillCircle(64, 64, 30, ST77XX_CYAN);
  tft1.setTextColor(ST77XX_WHITE);
  tft1.setCursor(36, 58);
  tft1.print("TFT1");

  tft2.fillRoundRect(14, 14, 100, 100, 8, ST77XX_GREEN);
  tft2.fillCircle(64, 64, 30, ST77XX_YELLOW);
  tft2.setTextColor(ST77XX_BLACK);
  tft2.setCursor(36, 58);
  tft2.print("TFT2");
}

void setup() {
  Serial.begin(115200);
  delay(300);   // ให้ไฟเลี้ยงจอคงที่ก่อน init

  Serial.println(F("\n=== test_display: KMR1441 x2 ==="));
  Serial.println(F("TFT1: CS=D8, TFT2: CS=D4, DC=D3, RST=D0, MOSI=D7, SCK=D5"));
  Serial.println(F("สำคัญ: ขา BL ของแต่ละจอต้องต่อ 3.3V (ไม่ต่อจอมืด/ขาว ไม่มีภาพ)"));
#if TFT_USE_ST7789
  Serial.println(F("Driver: ST7789"));
#else
  Serial.println(F("Driver: ST7735"));
#endif
  Serial.println(F("ถ้าไม่มีภาพเลย: 1) ต่อ BL->3.3V  2) ลอง TFT_USE_ST7789=1  3) ลอง TFT_INIT_TAB อื่น"));

  SPI.begin();
  hardwareResetDisplays();
  initDisplays();
  delay(100);
  // แสดงแดงทั้งจอสั้นๆ เพื่อเช็กว่ามีภาพ (ถ้าเห็นแดง = จอทำงาน)
  tft1.fillScreen(ST77XX_RED);
  tft2.fillScreen(ST77XX_RED);
  delay(500);
  tft1.fillScreen(ST77XX_BLACK);
  tft2.fillScreen(ST77XX_BLACK);
  Serial.println(F("Init done. Running test..."));
}

void loop() {
  // 1) แถบสี + ข้อความ
  screenBars();
  delay(TEST_DELAY_MS);

  // 2) เต็มจอสี
  screenSolid(ST77XX_RED, "TFT1 RED", "TFT2 RED");
  delay(TEST_DELAY_MS);
  screenSolid(ST77XX_GREEN, "TFT1 GRN", "TFT2 GRN");
  delay(TEST_DELAY_MS);
  screenSolid(ST77XX_BLUE, "TFT1 BLU", "TFT2 BLU");
  delay(TEST_DELAY_MS);

  // 3) รูปทรง
  screenShapes();
  delay(TEST_DELAY_MS);

  // 4) ขาว/ดำ
  screenSolid(ST77XX_WHITE, "TFT1", "TFT2");
  delay(TEST_DELAY_MS);
  screenSolid(ST77XX_BLACK, "TFT1", "TFT2");
  tft1.setTextColor(ST77XX_WHITE);
  tft2.setTextColor(ST77XX_WHITE);
  tft1.setCursor(52, 60);
  tft2.setCursor(52, 60);
  tft1.print("OK");
  tft2.print("OK");
  delay(TEST_DELAY_MS);
}
