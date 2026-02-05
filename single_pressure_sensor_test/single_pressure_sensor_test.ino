
//max value: 4095
//Sleep: 0

// The read value is for yours (2 sheet) is:
// Base: about 400-450
// Pressed: anywhere from 800 - 
// Lightly - pressed (actually useful): 1300 -

// The read value is for mine (1 sheet) is:
// Base: about 1750
// Pressed: anywhere from 1900 -
// Lightly - pressed (actually useful): 2300 -

int read_value_1;
int read_value_2;
const int PIN_1 = A0;
const int PIN_2 = A2;

void setup() { 
  Serial.begin(115200); 
  analogReadResolution(12); 
}

void if_pressed(int value) {
  if (value > 800) {
    Serial.println("Pressed");
  }
}

void print_values(int value1, int value2) {
  Serial.println("Values:");
  Serial.println(value1);
  Serial.println(value2);
}

void loop() { 
  read_value_1 = analogRead(PIN_1);
  read_value_2 = analogRead(PIN_2);
  print_values(read_value_1, read_value_2);
  delay(200); 
}
