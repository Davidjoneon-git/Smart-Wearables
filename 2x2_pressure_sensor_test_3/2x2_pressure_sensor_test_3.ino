const int rows[2] = {A0, A1};
const int cols[2] = {A3, A2};

// NxN grid (for expansion purposes)
const int n = 2;

const int rows_on_value[2][2] = {{1500, 1500},{1500, 1500}};

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
  for (int r = 0; r < n; r++) {
    // floating all rows
    for (int i = 0; i < n; i++) {
      pinMode(rows[i], INPUT);
    }
    pinMode(rows[r], OUTPUT);
    digitalWrite(rows[r], LOW);

    delayMicroseconds(200);

    int v[n] = {0};
    for (int i = 0; i < n; i++) {
      v[i] =analogRead(cols[i]);
    }

    for (int i = 0; i < n; i++) {
      if (v[i] < rows_on_value[r][i]) {
        Serial.print(r);
        Serial.print(": ");
        Serial.print(i);
        Serial.print("-");
        Serial.println("Active");
      }
    }
  }
  Serial.println("----");
  delay(200);
}
