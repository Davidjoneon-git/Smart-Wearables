#include <Arduino.h>

// ====== EDIT THESE FOR YOUR WIRING ======
// ADC input (avoid GPIO4 touch pin; use GPIO1/2/3)
static const int PIN_AIN   = 1;   // GPIO1 = A0 on XIAO ESP32-S3

// Drive pin into RowMUX COM
static const int PIN_DRV   = 44;  // example GPIO44 (D7)

// RowMUX control pins
static const int PIN_ROW_S0 = 43; // example GPIO43 (D6)
static const int PIN_ROW_EN = 9;  // example: GPIO8

// ColMUX control pins
static const int PIN_COL_S0 = 8;  // example GPIO6
static const int PIN_COL_EN = 7;  // example GPIO3

// Matrix size
static const uint8_t NROWS = 2;
static const uint8_t NCOLS = 2;

// ====== TUNING ======
static const uint16_t SETTLE_US = 500;  // 300-2000us typical, can go higher if slow is ok
static const uint8_t  NSAMPLES  = 7;    // more samples = smoother but slower
static const uint16_t CELL_DELAY_MS = 0; // extra delay per cell if you truly don't mind slowness

// CD4051 enable is active LOW: LOW = enabled, HIGH = disabled
inline void muxEnable(int enPin)  { digitalWrite(enPin, LOW); }
inline void muxDisable(int enPin) { digitalWrite(enPin, HIGH); }

// Write address bits to a mux (0..7)
void setMuxAddr(int s0, int s1, int s2, uint8_t ch) {
  if (s0 >= 0) digitalWrite(s0, (ch & 0x01) ? HIGH : LOW);
  if (s1 >= 0) digitalWrite(s1, (ch & 0x02) ? HIGH : LOW);
  if (s2 >= 0) digitalWrite(s2, (ch & 0x04) ? HIGH : LOW);
}

float alpha = 0.3; // bigger = faster change
float filtered[2][2] = {0.0};
float low_pass_filter(int row, int col, int raw) {
  filtered[row][col] = alpha * raw + (1.0 - alpha) * filtered[row][col];
  return filtered[row][col];
}

int readAveraged() {
  // Discard first read after switching (ESP32 ADC + mux settle)
  (void)analogRead(PIN_AIN);

  uint32_t sum = 0;
  for (uint8_t i = 0; i < NSAMPLES; i++) {
    sum += analogRead(PIN_AIN);
  }
  return (int)(sum / NSAMPLES);
}

// Read one cell (row, col) by selecting it physically then measuring
int readCell(uint8_t row, uint8_t col) {
  // Disconnect everything while switching addresses
  muxDisable(PIN_ROW_EN);
  muxDisable(PIN_COL_EN);

  // Set addresses
  digitalWrite(PIN_ROW_S0, row ? HIGH : LOW);
  digitalWrite(PIN_COL_S0, col ? HIGH : LOW);

  // Connect column to ADC first, then connect row to driver
  muxEnable(PIN_COL_EN);
  muxEnable(PIN_ROW_EN);

  // Pull row LOW (AIN is pulled up to 3V3 through 1k)
  digitalWrite(PIN_DRV, LOW);

  delayMicroseconds(SETTLE_US);
  if (CELL_DELAY_MS) delay(CELL_DELAY_MS);

  int v = readAveraged();

  // Optional: disconnect row immediately after read to reduce coupling
  muxDisable(PIN_ROW_EN);

  return v;
}

void setup() {
  Serial.begin(9600);

  // ESP32-S3 ADC configuration for 0..3.3V use
  analogReadResolution(12);            // 0..4095
  analogSetAttenuation(ADC_11db);
  analogSetPinAttenuation(PIN_AIN, ADC_11db);

  pinMode(PIN_DRV, OUTPUT);
  digitalWrite(PIN_DRV, LOW);

  // Set pin modes for mux controls
  pinMode(PIN_ROW_S0, OUTPUT);
  pinMode(PIN_ROW_EN, OUTPUT);

  pinMode(PIN_COL_S0, OUTPUT);
  pinMode(PIN_COL_EN, OUTPUT);

  muxDisable(PIN_ROW_EN);
  muxDisable(PIN_COL_EN);

  Serial.println("Per-cell scan starting...");
}

void loop() {
  for (uint8_t r = 0; r < NROWS; r++) {
    for (uint8_t c = 0; c < NCOLS; c++) {
      int v = readCell(r, c);
      Serial.printf("(%d,%d)=%.2f  ", r, c, low_pass_filter(r,c, v));
    }
    Serial.println();
  }
  Serial.println("----");
  delay(100); // whole-matrix scan rate (10 Hz here). Increase if you want slower.
}
