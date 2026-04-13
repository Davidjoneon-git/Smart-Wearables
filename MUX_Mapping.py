import asyncio
import struct
from bleak import BleakScanner, BleakClient
import numpy as np
import tensorflow as tf

N=8

#should be adjusted based on readings
threshold_ADC = 0

# new ML model should be built after each import!!!
model = tf.keras.models.load_model("ml_model.keras")

DEVICE_NAME = "XIAO-ESP32S3"
CHAR_UUID = "abcdefab-1234-1234-1234-abcdefabcdef"

NUM_VALUES = 65  # 1 backspace + 64 matrix values
PACKET_FORMAT = "<65H"  # little-endian, 65 unsigned shorts
PACKET_SIZE = struct.calcsize(PACKET_FORMAT)


# Extra ADC value that mimics pressed value
PlusADC = 500

def MatrixToBoolean(readings):
    global BaselineMatrix
    output = np.zeros((1, N, N), dtype=bool)
    
    # converts ADC values into Boolean values
    for r in range(N):
        for c in range(N):
            output[:, r, c] = readings[:, r, c] > (BaselineMatrix[r,c] + PlusADC)
    
    return output

# This should be redone
# Not updating the values in a list, but adding new layers into an np.array and when needed collapse them.
# This would eliminate false readings a bit
retained = np.zeros((1, N, N), dtype=int)
def update_matrix(readings):
    global retained
    
    # Collects the values
    for r in range(N):
        for c in range(N):
            retained[:, r, c] = max(readings[r][c], retained[:, r, c])


# Handles all incoming BLE data
def handle_notification(sender, data):
    global times, retained
    if len(data) != PACKET_SIZE:
        print(f"Wrong packet size: got {len(data)}, expected {PACKET_SIZE}")
        return

    values = struct.unpack(PACKET_FORMAT, data)

    # Incoming values
    backspace = values[0]
    matrix = values[1:]

    # Not really useful backspace check
    if backspace > threshold_ADC:
        print("Pressed")

    # Reshape into 8x8
    grid = [matrix[i*8:(i+1)*8] for i in range(8)]
    update_matrix(grid)

# Main function that connects with the ESP and recieves data periodically
async def main():
    print("Scanning...")
    devices = await BleakScanner.discover()

    target = None
    for d in devices:
        if d.name and DEVICE_NAME in d.name:
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