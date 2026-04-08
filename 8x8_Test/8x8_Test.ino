#include <Arduino.h>
#include <NimBLEDevice.h>

// GPIO numbers
static const int mux_in_S0 = A8;
static const int mux_in_S1 = A9;
static const int mux_in_S2 = A10;

static const int mux_com_in = A1;

static const int mux_out_S0 = A3;
static const int mux_out_S1 = A4;
static const int mux_out_S2 = A5;

static const int mux_com_out = A0;

static const int backspace = A2;

static const int inputMapping[8] = {1, 2, 3, 0, 4, 7, 5, 6};

// Matrix size
static const int n = 8;

// Setting the mux channel
void setMuxChannel(bool isOut, int channel)
{
  digitalWrite(isOut ? mux_out_S0 : mux_in_S0, channel & 0x01);
  digitalWrite(isOut ? mux_out_S1 : mux_in_S1, (channel >> 1) & 0x01);
  digitalWrite(isOut ? mux_out_S2 : mux_in_S2, (channel >> 2) & 0x01);
}

void setup()
{
  Serial.begin(9600);

  // Setting mux select pins as outputs
  pinMode(mux_in_S0, OUTPUT);
  pinMode(mux_in_S1, OUTPUT);
  pinMode(mux_in_S2, OUTPUT);

  pinMode(mux_out_S0, OUTPUT);
  pinMode(mux_out_S1, OUTPUT);
  pinMode(mux_out_S2, OUTPUT);

  pinMode(mux_com_out, OUTPUT);
  pinMode(mux_com_in, INPUT);
  digitalWrite(mux_com_out, LOW);
}

void loop()
{
  delay(250);
  int back = analogRead(backspace);
  Serial.print("Backspace: ");
  Serial.println(back);

  for (int i = 0; i < n; i++) {

    setMuxChannel(true, inputMapping[i]);
    delayMicroseconds(100);

    digitalWrite(mux_com_out, HIGH);
    for (int k = 0; k < n; k++) {

      setMuxChannel(false, inputMapping[k]);

      delayMicroseconds(100);

      int value = analogRead(mux_com_in);
    
      Serial.print(value);
      Serial.print(" ");
    }
    Serial.println("");
    Serial.println("----------------------------");
    
    digitalWrite(mux_com_out, LOW);
    // Small delay to let the signal settle
    delayMicroseconds(100);
  }
}
