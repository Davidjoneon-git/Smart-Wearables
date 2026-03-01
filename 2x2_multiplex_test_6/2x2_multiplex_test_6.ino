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

static const int backspace = A8;

// Matrix size
static const int n = 2;

static NimBLEUUID SERVICE_UUID("12345678-1234-1234-1234-1234567890ab");
static NimBLEUUID CHAR_UUID   ("abcdefab-1234-1234-1234-abcdefabcdef");

NimBLECharacteristic* pChar = nullptr;
bool deviceConnected = false;

class ServerCallbacks : public NimBLEServerCallbacks {
  void onConnect(NimBLEServer* pServer, NimBLEConnInfo& connInfo) override {
    deviceConnected = true;
  }
  void onDisconnect(NimBLEServer* pServer, NimBLEConnInfo& connInfo, int reason) override {
    deviceConnected = false;
    NimBLEDevice::startAdvertising();
  }
};

// Setting the mux channel
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
  Serial.begin(115200);

  NimBLEDevice::init("XIAO-ESP32S3");

  NimBLEServer* pServer = NimBLEDevice::createServer();
  pServer->setCallbacks(new ServerCallbacks());

  NimBLEService* pService = pServer->createService(SERVICE_UUID);

  pChar = pService->createCharacteristic(
    CHAR_UUID,
    NIMBLE_PROPERTY::READ | NIMBLE_PROPERTY::NOTIFY
  );

  pChar->createDescriptor("2902");

  pChar->setValue("0");

  pService->start();

  NimBLEAdvertising* pAdv = NimBLEDevice::getAdvertising();
  pAdv->addServiceUUID(SERVICE_UUID);
  pAdv->start();

  Serial.println("BLE started.");

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

  if (deviceConnected) {
    char buf[16];
    snprintf(buf, sizeof(buf), "%d", back);

    pChar->setValue((uint8_t*)buf, strlen(buf));
    pChar->notify();
  }

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
      if (deviceConnected) {
        char buf[16];
        snprintf(buf, sizeof(buf), "%d", value);

        pChar->setValue((uint8_t*)buf, strlen(buf));
        pChar->notify();
      }
      Serial.println(value);
    }
    Serial.println("----------------------------");
    
    digitalWrite(mux_com_out, LOW);
    // Small delay to let the signal settle
    delayMicroseconds(100);
  }
}
