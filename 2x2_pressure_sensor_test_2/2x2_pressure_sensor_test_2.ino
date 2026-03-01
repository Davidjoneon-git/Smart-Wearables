/*
  2x2 resistive sensor matrix using TWO CD4051 multiplexers
  - U1 = Row MUX (connects Arduino DRV to R0 or R1)
  - U2 = Column MUX (connects C0 or C1 to Arduino A0)
  - Uses 3.3V and a 1k resistor from A0 -> 3V3 (pull-up)
  - Drive is LOW (GND) through the selected row
  - CD4051 Enable (E̅ / INH) is ACTIVE LOW: LOW = enabled, HIGH = disabled

  Wiring recap:
  U1 (ROW MUX):
    pin16 VCC -> 3V3
    pin 8 GND -> GND
    pin 7 VEE -> GND
    pin 3 COM(A) -> DRV (D2)
    pin13 A0 -> R0
    pin14 A1 -> R1
    pin11 S0 -> D3
    pin10 S1 -> GND
    pin 9 S2 -> GND
    pin 6 E̅ -> D4

  U2 (COL MUX):
    pin16 VCC -> 3V3
    pin 8 GND -> GND
    pin 7 VEE -> GND
    pin 3 COM(A) -> A0 (analog in)
    pin13 A0 -> C0
    pin14 A1 -> C1
    pin11 S0 -> D5
    pin10 S1 -> GND
    pin 9 S2 -> GND
    pin 6 E̅ -> D6

  Divider:
    A0 -> 1k -> 3V3
    (optional) A0 -> 1nF..10nF -> GND
*/

const int DRV   = 2;   // Drive pin into RowMUX COM (U1 pin 3)
const int AIN   = A0;  // Analog input from ColMUX COM (U2 pin 3)

// Row MUX control (U1)
const int ROW_S0 = 3;  // U1 pin 11
const int ROW_EN = 4;  // U1 pin 6 (active LOW)

// Column MUX control (U2)
const int COL_S0 = 5;  // U2 pin 11
const int COL_EN = 6;  // U2 pin 6 (active LOW)

// Tunables
const unsigned int SETTLE_US = 200;  // settling time after switching

inline void muxEnable(int enPin)  { digitalWrite(enPin, LOW); }   // active LOW
inline void muxDisable(int enPin) { digitalWrite(enPin, HIGH); }  // active LOW

inline void selectRow(int row /*0..1*/) { digitalWrite(ROW_S0, row ? HIGH : LOW); }
inline void selectCol(int col /*0..1*/) { digitalWrite(COL_S0, col ? HIGH : LOW); }

int readA0Stable3x() {
  // First read after switching is often stale due to ADC sample/hold and mux settling
  (void)analogRead(AIN);
  int a = analogRead(AIN);
  int b = analogRead(AIN);
  int c = analogRead(AIN);
  return (a + b + c) / 3;
}

// Read one cell (row, col) where row and col are 0 or 1
int readCell(int row, int col) {
  // Disconnect while switching to reduce charge injection/ghost paths
  muxDisable(ROW_EN);
  muxDisable(COL_EN);

  // Select desired row/col
  selectRow(row);
  selectCol(col);

  // Connect the column to A0 first (sense path)
  muxEnable(COL_EN);

  // Connect the row to DRV (drive path)
  muxEnable(ROW_EN);

  // Drive LOW (because A0 is pulled up to 3V3 through 1k)
  digitalWrite(DRV, LOW);

  delayMicroseconds(SETTLE_US);

  // Read
  int v = readA0Stable3x();

  // Stop driving & disconnect row (optional, but helps between reads)
  muxDisable(ROW_EN);

  return v;
}

void setup() {
  Serial.begin(115200);

  pinMode(DRV, OUTPUT);
  digitalWrite(DRV, LOW);

  pinMode(ROW_S0, OUTPUT);
  pinMode(ROW_EN, OUTPUT);

  pinMode(COL_S0, OUTPUT);
  pinMode(COL_EN, OUTPUT);

  // Start disconnected
  muxDisable(ROW_EN);
  muxDisable(COL_EN);

  // Ensure select pins have defined states
  selectRow(0);
  selectCol(0);

  // NOTE: AIN (A0) is analog input, no pinMode needed
}

void loop() {
  int s00 = readCell(0, 0);
  int s01 = readCell(0, 1);
  int s10 = readCell(1, 0);
  int s11 = readCell(1, 1);

  Serial.print("S00="); Serial.print(s00);
  Serial.print("  S01="); Serial.print(s01);
  Serial.print("  S10="); Serial.print(s10);
  Serial.print("  S11="); Serial.println(s11);

  delay(50);
}