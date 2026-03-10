const int rows[2] = {A0, A1};
const int cols[2] = {A3, A2};

/**
Avg values (Idle):
Row 0: 2700 2850
Row 1: 2350 2250

Avg values (Active)(Soft):
Row 0: 1500 1500
Row 1: 1600 1300

Avg values (Active)(Hard):
Row 0: 400 450
Row 1: 500 300
*/

void setup() {
  Serial.begin(115200);

  // columns are inputs
  pinMode(cols[0], INPUT);
  pinMode(cols[1], INPUT);

  // start rows floating
  pinMode(rows[0], INPUT);
  pinMode(rows[1], INPUT);
}

void loop() {
  for (int r = 0; r < 2; r++) {
    // floating all rows
    pinMode(rows[0], INPUT);
    pinMode(rows[1], INPUT);

    pinMode(rows[r], OUTPUT);
    digitalWrite(rows[r], LOW);

    delayMicroseconds(200);

    int v0 = analogRead(cols[0]);
    int v1 = analogRead(cols[1]);

    Serial.print("Row "); Serial.print(r);
    Serial.print(": "); Serial.print(v0);
    Serial.print(" ");  Serial.println(v1);
  }
  Serial.println("----");
  delay(200);
}
