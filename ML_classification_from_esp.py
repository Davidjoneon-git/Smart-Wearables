import asyncio
import struct
from bleak import BleakScanner, BleakClient
import numpy as np
import tensorflow as tf

N=8

#should be adjusted based on readings
threshold_ADC = 1000

# new ML model should be built after each import!!!
model = tf.keras.models.load_model("ml_model.keras")

DEVICE_NAME = "XIAO-ESP32S3"
CHAR_UUID = "abcdefab-1234-1234-1234-abcdefabcdef"

NUM_VALUES = 65  # 1 backspace + 64 matrix values
PACKET_FORMAT = "<65H"  # little-endian, 65 unsigned shorts
PACKET_SIZE = struct.calcsize(PACKET_FORMAT)

#The inputs should be taken in intervals take the full picture (? sec = 1 image or ? reading = 1 image) (30 reading / sec)
#Maybe starting from a point of first pressed grid point
#this will have to be replaced with a func that turns ADC (0-4065) into bool (true or false)
def basic_bool(readings):
    output = np.zeros((1, N, N), dtype=bool)
    
    for r in range(N):
        for c in range(N):
            output[:, r, c] = readings[:, r, c] > threshold_ADC
    
    return output

retained = np.zeros((1, N, N), dtype=int)
def update_matrix(readings):
    global retained
    for r in range(N):
        for c in range(N):
            retained[:, r, c] = max(readings[r][c], retained[:, r, c])

max_times = 60 # about 3 sec
times = 0

def handle_notification(sender, data):
    global times, retained
    if len(data) != PACKET_SIZE:
        print(f"Wrong packet size: got {len(data)}, expected {PACKET_SIZE}")
        return

    values = struct.unpack(PACKET_FORMAT, data)

    backspace = values[0]
    matrix = values[1:]

    if backspace > threshold_ADC:
        print("Pressed")

    # Reshape into 8x8
    grid = [matrix[i*8:(i+1)*8] for i in range(8)]
    update_matrix(grid)
    times += 1
    if times == max_times:
        sample_bool = basic_bool(retained)
        sample_feat = sample_bool.reshape(-1, N * N).astype(np.float32)
        prediction = model.predict(sample_feat)
        predicted_digit = np.argmax(prediction, axis=1)[0]
        print(f"Predicted Digit: {predicted_digit}")
        retained = np.zeros((1, N, N), dtype=int)
        times = 0

async def main():
    print("Scanning...")
    devices = await BleakScanner.discover()

    target = None
    for d in devices:
        if d.name == DEVICE_NAME:
            target = d
            break

    if target is None:
        print("Device not found")
        return

    async with BleakClient(target.address) as client:
        print("Connected to", target.name)
        await client.start_notify(CHAR_UUID, handle_notification)

        while True:
            await asyncio.sleep(1)

asyncio.run(main())