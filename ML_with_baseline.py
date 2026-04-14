import asyncio
import struct
from bleak import BleakScanner, BleakClient
import numpy as np
import tensorflow as tf

N = 8

# should be adjusted based on readings
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

# number of readings for a single deciding
max_times = 60

# number of collected samples for baseline
baselineReadingsNum = 80

# confidence threshold for "null"
nullThreshold = 0.7

# reading index
times = 0

# Is collecting data for baseline
IsBaseline = True

# Buffers only for baseline creation
BaselineMatrixFrames = []
BaselineBackspaceFrames = []

# Will be created after baseline collection
BaselineMatrix = np.zeros((N, N), dtype=np.float32)
BaselineBackspace = 0.0

# Retained matrix for inference stage
retained = np.zeros((1, N, N), dtype=int)


def MatrixToBoolean(readings):
    global BaselineMatrix
    output = np.zeros((1, N, N), dtype=bool)

    # converts ADC values into Boolean values
    for r in range(N):
        for c in range(N):
            output[:, r, c] = readings[:, r, c] > (BaselineMatrix[r, c] + PlusADC)

    return output


def update_matrix(readings):
    global retained

    # Collect maximum values over the current decision window
    for r in range(N):
        for c in range(N):
            retained[0, r, c] = max(readings[r][c], retained[0, r, c])


def CreateBaselineData(backspace, matrix):
    global IsBaseline, times, BaselineMatrix, BaselineBackspace

    # reshape incoming flat 64 values into 8x8
    matrix_2d = np.array(matrix, dtype=np.float32).reshape(N, N)

    BaselineMatrixFrames.append(matrix_2d)
    BaselineBackspaceFrames.append(backspace)

    times += 1
    print(f"Baseline frame {times}/{baselineReadingsNum}")

    if times >= baselineReadingsNum:
        IsBaseline = False
        times = 0

        # shape -> (num_frames, N, N)
        Mbuffer = np.array(BaselineMatrixFrames, dtype=np.float32)
        Bbuffer = np.array(BaselineBackspaceFrames, dtype=np.float32)

        # collapse with median
        BaselineMatrix = np.median(Mbuffer, axis=0)
        BaselineBackspace = np.median(Bbuffer)

        # clear buffers
        BaselineMatrixFrames.clear()
        BaselineBackspaceFrames.clear()

        print("\nBaseline finished")
        print("BaselineBackspace:", BaselineBackspace)
        print("BaselineMatrix:")
        for row in BaselineMatrix:
            print(row)


# Handles all incoming BLE data
def handle_notification(sender, data):
    global times, retained, IsBaseline

    if len(data) != PACKET_SIZE:
        print(f"Wrong packet size: got {len(data)}, expected {PACKET_SIZE}")
        return

    values = struct.unpack(PACKET_FORMAT, data)

    # Incoming values
    backspace = values[0]
    matrix = values[1:]   # flat 64 values

    # First baselineReadingsNum readings go here
    if IsBaseline:
        CreateBaselineData(backspace, matrix)
        return

    # Optional backspace check
    if backspace > threshold_ADC:
        print("Pressed")

    # reshape into 8x8
    grid = np.array(matrix, dtype=np.int32).reshape(N, N)
    update_matrix(grid)

    times += 1

    # Checks if it should decide on a number
    if times >= max_times:
        sample_bool = MatrixToBoolean(retained)
        sample_feat = sample_bool.reshape(-1, N * N).astype(np.float32)

        prediction = model.predict(sample_feat, verbose=0)
        y_pred = np.argmax(prediction, axis=1)
        confidences = np.max(prediction, axis=1)

        predicted_digit = np.where(confidences >= nullThreshold, y_pred, -1)[0]
        print(f"Predicted Digit: {predicted_digit}, confidence: {confidences[0]}")

        retained = np.zeros((1, N, N), dtype=int)
        times = 0


# Main function that connects with the ESP and receives data periodically
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