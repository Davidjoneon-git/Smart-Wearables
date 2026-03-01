/*
  XIAO ESP32-S3 + 2x CD4051 + 2x2 resistive matrix (anti-sneak-path style)

  Hardware method:
  - AIN (GPIO1) is pulled UP to 3V3 via 1k
  - Selected row is pulled DOWN (DRV = LOW) through RowMUX
  - Selected column is connected to AIN through ColMUX
  - Pressing/lowering sensor resistance pulls AIN downward -> ADC drops

  CD4051:
  - E̅ is active LOW: LOW = enabled, HIGH = disabled
  - S1 and S2 tied to GND (we only use channels 0 and 1)
*/

#include <Arduino.h>

// --- XIAO pin choices (match wiring above) ---
static const int PIN_AIN   = 1;   // GPIO1 = A0 (ADC input)
static const int PIN_DRV   = 44;  // GPIO44 = D7 (drive into RowMUX COM)

static const int PIN_ROW_S0 = 43; // GPIO43 = D6 (RowMUX S0)
static const int PIN_ROW_EN = 9;  // GPIO9  = D10 (RowMUX E̅)

static const int PIN_COL_S0 = 8;  // GPIO8  = D9 (ColMUX S0)
static const int PIN_COL_EN = 7;  // GPIO7  = D8 (ColMUX E̅)

// Tunables
static const uint16_t SETTLE_US = 300;  // allow mux + ADC to settle

inline void muxEnable(int enPin)  { digitalWrite(enPin, LOW); }   // active LOW
inline void muxDisable(int enPin) { digitalWrite(enPin, HIGH); }  // active LOW

inline void selectRow(uint8_t row) { digitalWrite(PIN_ROW_S0, row ? HIGH : LOW); }
inline void selectCol(uint8_t col) { digitalWrite(PIN_COL_S0, col ? HIGH : LOW); }

int readAinStable() {
  // First read after switching is often stale; ESP32 ADC is also a bit noisy
  (void)analogRead(PIN_AIN);
  int a = analogRead(PIN_AIN);
  int b = analogRead(PIN_AIN);
  int c = analogRead(PIN_AIN);
  return (a + b + c) / 3;
}

int readCell(uint8_t row, uint8_t col) {
  // Disconnect while changing addresses to reduce transients / sneak effects
  muxDisable(PIN_ROW_EN);
  muxDisable(PIN_COL_EN);

  selectRow(row);
  selectCol(col);

  // Connect sense first, then drive
  muxEnable(PIN_COL_EN);
  muxEnable(PIN_ROW_EN);

  // Pull selected row LOW (AIN is pulled up via 1k)
  digitalWrite(PIN_DRV, LOW);

  delayMicroseconds(SETTLE_US);

  int v = readAinStable();

  // Stop driving between reads (helps reduce cross-coupling)
  muxDisable(PIN_ROW_EN);

  return v;
}

void setup() {
  Serial.begin(115200);

  // ESP32-S3 ADC setup
  analogReadResolution(12);            // 0..4095
  analogSetAttenuation(ADC_11db);      // better full-range for ~0..3.3V
  // Optional: apply attenuation specifically to this pin too
  analogSetPinAttenuation(PIN_AIN, ADC_11db);

  pinMode(PIN_DRV, OUTPUT);
  digitalWrite(PIN_DRV, LOW);

  pinMode(PIN_ROW_S0, OUTPUT);
  pinMode(PIN_ROW_EN, OUTPUT);
  pinMode(PIN_COL_S0, OUTPUT);
  pinMode(PIN_COL_EN, OUTPUT);

  muxDisable(PIN_ROW_EN);
  muxDisable(PIN_COL_EN);

  selectRow(0);
  selectCol(0);

  Serial.println("Starting 2x2 scan...");
}

void loop() {
  int s00 = readCell(0, 0);
  int s01 = readCell(0, 1);
  int s10 = readCell(1, 0);
  int s11 = readCell(1, 1);

  Serial.printf("S00=%4d  S01=%4d  S10=%4d  S11=%4d\n", s00, s01, s10, s11);
  delay(50);
}
