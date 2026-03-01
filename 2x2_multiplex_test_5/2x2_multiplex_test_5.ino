#include <Arduino.h>
#include <NimBLEDevice.h>

// GPIO numbers
static const int mux_in_S0 = A5;
static const int mux_in_S1 = -1;
static const int mux_in_S2 = -1;

static const int mux_com_in = A0;

static const int mux_out_S0 = A9;
static const int mux_out_S1 = -1;
static const int mux_out_S2 = -1;

static const int mux_com_out = A2;

// Matrix size
static const int n = 2;

// Set the mux channel (0–7)
void setMuxChannel(bool isOut, int channel)
{
  digitalWrite(isOut ? mux_out_S0 : mux_in_S0, channel & 0x01);
  if (n>2) {
    digitalWrite(isOut ? mux_out_S1 : mux_in_S1, (channel >> 1) & 0x01);
    digitalWrite(isOut ? mux_out_S2 : mux_in_S2, (channel >> 2) & 0x01);
  }
}

void setup()
{
  // Initialize serial communication
  Serial.begin(115200);

  // Set mux select pins as outputs
  pinMode(mux_in_S0, OUTPUT);
  pinMode(mux_in_S1, OUTPUT);
  pinMode(mux_in_S2, OUTPUT);

  pinMode(mux_out_S0, OUTPUT);
  pinMode(mux_out_S1, OUTPUT);
  pinMode(mux_out_S2, OUTPUT);

  pinMode(mux_com_out, OUTPUT);
  pinMode(mux_com_in, INPUT);
  digitalWrite(mux_com_out, LOW);

  Serial.println("setup Done");
}

static const int press_value = 2700;

void loop()
{
  delay(250);

  for (int i = 0; i < n; i++) {

    setMuxChannel(true, i);
    delayMicroseconds(100);

    digitalWrite(mux_com_out, HIGH);
    for (int k = 0; k < n; k++) {

      setMuxChannel(false, k);

      delayMicroseconds(100);

      int value = analogRead(mux_com_in);

      Serial.print("Row: ");
      Serial.print(i+1);
      Serial.print(", Col:");
      Serial.print(k+1);
      Serial.print(": ");
      /**
      if (value > press_value) {
        Serial.println("TRUE");
      } else {
        Serial.println("FALSE");
      }
      */
      Serial.println(value);
    }
    Serial.println("----------------------------");
    
    digitalWrite(mux_com_out, LOW);
    // Small delay to let the signal settle
    delayMicroseconds(100);
  }
}
