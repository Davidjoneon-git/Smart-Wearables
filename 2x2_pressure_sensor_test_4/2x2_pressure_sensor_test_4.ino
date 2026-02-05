const int rows[2] = {A0, A1};
const int cols[2] = {A3, A2};

// NxN grid (for expansion purposes)
const int n = 2;

const int rows_on_value[2][2] = {{1500, 1500},{1500, 1500}};
int rows_active_value[2][2];
int wiggle = 100;
int treshhold = 1000;

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

  delay(100);

  for (int r = 0; r < n; r++) {
    // float all rows
    for (int i = 0; i < n; i++) {
      pinMode(rows[i], INPUT);
    }

    // activate row r
    pinMode(rows[r], OUTPUT);
    digitalWrite(rows[r], LOW);
    delayMicroseconds(300);

    for (int c = 0; c < n; c++) {
      long sum = 0;
      for (int k = 0; k < 16; k++) {
        sum += analogRead(cols[c]);
      }
      int baseline = sum / 16;

      // threshold below idle baseline
      rows_active_value[r][c] = baseline - treshhold;
    }
  }

  Serial.println("Calibration done:");
}

// should be implemented better
/**
We need to triangulate the source to avoid phantom - presses:
in 2x2 if 3 of them are pressed, due to the change in the data, it detects the 4. as pressed (with weak implementation).

Every single datapoint relates to another,
therefore we need some kind of baseline "values"
for what is considered pressed if some sensors are already active
*/
bool is_in_range(int value, int target) {
  if (value > target) {
    if ((value - wiggle) > target) {
      return false;
    } else {
      return true;
    }
  } else {
    if ((value + wiggle) < target) {
      return false;
    } else {
      return true;
    }
  }
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
      Serial.println(v[i]);
      /**
      if (is_in_range(v[i], rows_active_value[r][i])) {
        Serial.print(r);
        Serial.print(": ");
        Serial.print(i);
        Serial.print("-");
        Serial.println("Active");
      }
      */
    }
  }
  Serial.println("----");
  delay(200);
}
