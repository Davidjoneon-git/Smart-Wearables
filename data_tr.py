import asyncio
import struct
import numpy as np
import tkinter as tk
from bleak import BleakScanner, BleakClient

DEVICE_NAME = "XIAO-ESP32S3"
CHAR_UUID = "abcdefab-1234-1234-1234-abcdefabcdef"

NUM_VALUES = 65  # 1 backspace + 64 matrix values
PACKET_FORMAT = "<65H"  # little-endian, 65 unsigned shorts
PACKET_SIZE = struct.calcsize(PACKET_FORMAT)

def handle_notification(sender, data):
    if len(data) != PACKET_SIZE:
        print(f"Wrong packet size: got {len(data)}, expected {PACKET_SIZE}")
        return

    values = struct.unpack(PACKET_FORMAT, data)

    backspace = values[0]
    matrix = values[1:]

    if IsBaseline:
        CreateBaselineData(backspace, matrix)
        return
    
    grid = [matrix[i*8:(i+1)*8] for i in range(8)]
    
    isBackSpace = backspace>(BaselineBackspace*PlusADC)

    print("Backspace:", isBackSpace)
    if isBackSpace:
        print("-" * 40)
        return

    grid = [matrix[i*8:(i+1)*8] for i in range(8)]
    for row in MatrixToBoolean(grid):
        print(row)
    print("-" * 40)

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



# Extra ADC value that mimics pressed value
PlusADC = 1.1

def MatrixToBoolean(readings):
    global BaselineMatrix
    output = []
    
    # converts ADC values into Boolean values
    for r in range(N):
        temp = []
        for c in range(N):
            if (readings[r][c] > (BaselineMatrix[r,c] * PlusADC)):
                temp.append(1)
            else:
                temp.append(0)
        output.append(temp)
    return output

N = 8

# number of readings for a single deciding
max_times = 60

# reading index
times = 0

# number of collected sample for baseline
baselineReadingsNum = 60

# Is collecting data for baseline
IsBaseline = True

# Buffers only for baseline creation
BaselineMatrixFrames = []
BaselineBackspaceFrames =[]

def CreateBaselineData(backspace, matrix):
    global IsBaseline, times, BaselineMatrix, BaselineBackspace
    
    BaselineMatrixFrames.append(matrix)
    BaselineBackspaceFrames.append(backspace)
    
    times += 1
    print(times)
    
    if times >= baselineReadingsNum:
        IsBaseline = False
        times = 0
        
        # Creates Numpy.Array(len(Frames), N, N)
        Mbuffer = np.array(BaselineMatrixFrames)
        Bbuffer = np.array(BaselineBackspaceFrames)
        
        # Collapses them with median into Numpy.Array(1, N, N)
        BaselineMatrix = np.median(Mbuffer, axis = 0).reshape(N, N)
        BaselineBackspace = np.median(Bbuffer, axis = 0)
        
        # Clears them for efficiency (not really needed, but nice)
        BaselineMatrixFrames.clear()
        BaselineBackspaceFrames.clear()
        
        print(BaselineBackspace)
        grid = [BaselineMatrix[i*8:(i+1)*8] for i in range(8)]
        for row in grid:
            print(row)
        
        return


asyncio.run(main())