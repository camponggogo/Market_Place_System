/*
 * test_ST7735S.ino - ทดสอบจอ ST7735S (2 จอ) บน ESP8266
 * Board: D1 MINI PRO (ESP-8266EX) หรือ NodeMCU / ESP-12E
 *
 * จอ: ST7735S 1.44" 128x128 SPI (เช่น KMR1441_SPI V2)
 * ใช้เฉพาะ Adafruit ST7735 (ไม่มี ST7789)
 *
 * Pinout (D1 Mini Pro):
 *   TFT1: CS=D8(15), DC=D3(0), RST=D0(16)
 *   TFT2: CS=D4(2),  DC=D3(0), RST=D0(16)
 *   SPI:  MOSI=D7(13), SCK=D5(14)
 *   BL แต่ละจอ -> 3.3V
 *
 * ไลบรารี: Adafruit ST7735 and ST7789 Library, Adafruit GFX, SPI
 * Board: LOLIN(WEMOS) D1 mini Pro (ESP8266) หรือ Generic ESP8266 Module
 */

#include <Adafruit_GFX.h>
#include <Adafruit_ST7735.h>
#include <SPI.h>

// ============== PINOUT (ESP8266 D1 Mini Pro) ==============
#define TFT1_CS   15   // D8
#define TFT1_DC   0    // D3 A0
#define TFT1_RST  16   // D0
#define TFT2_CS   2    // D4
#define TFT2_DC   0
#define TFT2_RST  16

// ============== ST7735S Init ==============
// จอ 1.44" 128x128 (ST7735S) มักใช้ GREENTAB หรือ 144GREENTAB
// ไม่มีภาพ/ลาย/ขาว: ลองสลับตามลำดับ INITR_144GREENTAB -> INITR_GREENTAB -> INITR_BLACKTAB -> INITR_18GREENTAB
#define TFT_INIT_TAB  INITR_144GREENTAB

Adafruit_ST7735 tft1 = Adafruit_ST7735(TFT1_CS, TFT1_DC, TFT1_RST);
Adafruit_ST7735 tft2 = Adafruit_ST7735(TFT2_CS, TFT2_DC, TFT2_RST);

#define TEST_DELAY_MS  2000
#define TFT_INVERT_DISPLAY  0   // 1 = สีกลับกัน

void hardwareResetDisplays() {
  pinMode(TFT1_RST, OUTPUT);
  digitalWrite(TFT1_RST, LOW);
  delay(50);
  digitalWrite(TFT1_RST, HIGH);
  delay(150);
}

void initDisplays() {
  tft1.initR(TFT_INIT_TAB);
  tft2.initR(TFT_INIT_TAB);
  tft1.setRotation(1);
  tft2.setRotation(1);
#if TFT_INVERT_DISPLAY
  tft1.invertDisplay(true);
  tft2.invertDisplay(true);
#endif
  tft1.setTextSize(1);
  tft2.setTextSize(1);
}

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
  tft2.setCursor(20, 56);
  tft1.setTextSize(2);
  tft2.setTextSize(2);
  tft1.print(label1);
  tft2.print(label2);
}

void screenBars() {
  tft1.fillScreen(ST77XX_BLACK);
  tft1.drawRect(0, 0, 128, 128, ST77XX_WHITE);
  tft1.setTextColor(ST77XX_WHITE);
  tft1.setCursor(16, 4);
  tft1.setTextSize(2);
  tft1.print("ST7735S #1");
  tft1.setCursor(40, 24);
  tft1.setTextSize(1);
  tft1.print("128x128");
  tft1.fillRect(10, 38, 108, 18, ST77XX_BLUE);
  tft1.fillRect(10, 58, 108, 18, ST77XX_GREEN);
  tft1.fillRect(10, 78, 108, 18, ST77XX_RED);
  tft1.setCursor(10, 102);
  tft1.print("ESP8266");

  tft2.fillScreen(ST77XX_BLACK);
  tft2.drawRect(0, 0, 128, 128, ST77XX_WHITE);
  tft2.setTextColor(ST77XX_WHITE);
  tft2.setCursor(16, 4);
  tft2.setTextSize(2);
  tft2.print("ST7735S #2");
  tft2.setCursor(40, 24);
  tft2.setTextSize(1);
  tft2.print("128x128");
  tft2.fillRect(10, 38, 108, 18, ST77XX_BLUE);
  tft2.fillRect(10, 58, 108, 18, ST77XX_GREEN);
  tft2.fillRect(10, 78, 108, 18, ST77XX_RED);
  tft2.setCursor(10, 102);
  tft2.print("ESP8266");
}

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
  delay(300);

  Serial.println(F("\n=== test_ST7735S (ESP8266) ==="));
  Serial.println(F("TFT1: CS=D8, TFT2: CS=D4, DC=D3, RST=D0, MOSI=D7, SCK=D5"));
  Serial.println(F("BL -> 3.3V (ทั้งสองจอ)"));
  Serial.println(F("ไม่มีภาพ: เปลี่ยน TFT_INIT_TAB เป็น INITR_GREENTAB, INITR_BLACKTAB หรือ INITR_18GREENTAB"));

  SPI.begin();
  hardwareResetDisplays();
  initDisplays();
  delay(100);

  tft1.fillScreen(ST77XX_RED);
  tft2.fillScreen(ST77XX_RED);
  delay(500);
  tft1.fillScreen(ST77XX_BLACK);
  tft2.fillScreen(ST77XX_BLACK);
  Serial.println(F("Init OK. Test loop..."));
}

void loop() {
  screenBars();
  delay(TEST_DELAY_MS);

  screenSolid(ST77XX_RED,   "RED",   "RED");
  delay(TEST_DELAY_MS);
  screenSolid(ST77XX_GREEN, "GREEN", "GREEN");
  delay(TEST_DELAY_MS);
  screenSolid(ST77XX_BLUE, "BLUE",  "BLUE");
  delay(TEST_DELAY_MS);

  screenShapes();
  delay(TEST_DELAY_MS);

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
