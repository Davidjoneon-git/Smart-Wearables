import asyncio
import struct
import numpy as np
from bleak import BleakScanner, BleakClient

DEVICE_NAME = "XIAO-ESP32S3"
CHAR_UUID = "abcdefab-1234-1234-1234-abcdefabcdef"

NUM_VALUES = 65  # 1 backspace + 64 matrix values
PACKET_FORMAT = "<65H"  # little-endian, 65 unsigned shorts
PACKET_SIZE = struct.calcsize(PACKET_FORMAT)

Done = False

# number of collected samples for baseline = 80
baselineReadingsNum = 60

# Is collecting data for baseline
IsBaseline = True

# Buffers only for baseline creation
BaselineMatrixFrames = []
BaselineBackspaceFrames = []

# Will be created after baseline collection
BaselineMatrix = np.zeros((8, 8), dtype=np.float32)
BaselineBackspace = 0.0

times = 0
def CreateBaselineData(backspace, matrix):
    global IsBaseline, times, BaselineMatrix, BaselineBackspace

    BaselineMatrixFrames.append(matrix)
    BaselineBackspaceFrames.append(backspace)

    times += 1
    print(f"Baseline frame {times}/{baselineReadingsNum}")

    if times >= baselineReadingsNum:
        IsBaseline = False
        times = 0

        # shape -> (num_frames, 8, 8)
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

async def main():
    global Done
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

        while not Done:
            await asyncio.sleep(1)


CurrentReadingFeature = "0"
collectionN = 0

def handle_notification(sender, data):
    global collectionN, collection, Done, Collecting
    if len(data) != PACKET_SIZE:
        print(f"Wrong packet size: got {len(data)}, expected {PACKET_SIZE}")
        return

    values = struct.unpack(PACKET_FORMAT, data)

    backspace = values[0]
    matrix = np.array(values[1:], dtype=np.float32).reshape(8,8)
    
    if backspace > 500:
        print("Collection Started")
        Collecting = True
    
    if IsBaseline:
        CreateBaselineData(backspace, matrix)
        return
    
    if CollectingReading(matrix):
        collectionN += 1
        if collectionN >= CollectedReadingAmount:
            arr = np.array(collection, dtype=np.float32)
            np.save(CurrentReadingFeature, arr)
            print("Readings have been saved")
            Done = True
            

CollectedReadingAmount = 60
SamplesPerReading = 60
collection = []
readings = []
Collecting = False

read = 0
def CollectingReading(matrix):
    global readings, read, collection, Collecting
    if not Collecting:
        return False
    
    newMatrix = matrix - BaselineMatrix
    readings.append(newMatrix)
    read += 1
    
    if read >= SamplesPerReading:
        print(f"Reading added to collection: {read}")
        collection.append(readings)
        readings = []
        read = 0
        Collecting = False
        return True
    return False


asyncio.run(main())