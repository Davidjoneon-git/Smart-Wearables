import tkinter as tk
from tkinter import ttk
import tensorflow as tf
import numpy as np
import asyncio
import struct
import calculator
import tkinter.font as tkFont
from bleak import BleakScanner, BleakClient

DEVICE_NAME = "XIAO-ESP32S3"
CHAR_UUID = "abcdefab-1234-1234-1234-abcdefabcdef"

NUM_VALUES = 65
PACKET_FORMAT = "<65H"
PACKET_SIZE = struct.calcsize(PACKET_FORMAT)

Font = ("Arial", 12)
Parts = [1, 2, 3, " + ", 3, 4, " - ", 4, 3, " - ", 3, 3, " + ", 3, 3, 3, 3]

Menu = None
DeviceConnectionTop = None
DeviceConnectionTopLabel = None
top = None

# new ML model should be built after each import!!!
model = tf.keras.models.load_model("ml_model.keras")

N=8

# confidence threshold for "null"
nullThreshold = 0.7

# number of collected samples for baseline
baselineReadingsNum = 80

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

max_times = 60

times = 0
        
def Threshold(value : int):
    maxADC = 4096
    exp = 0.84
    center = maxADC/2
    base = 400
    d = abs(value - center) / center
        
    return (max(0, base * (1 - d**exp)))
    

def MatrixToBoolean(readings):
    global BaselineMatrix
    output = np.zeros((1, N, N), dtype=bool)

    # converts ADC values into Boolean values
    for r in range(N):
        for c in range(N):
            output[:, r, c] = readings[:, r, c] > Threshold(BaselineMatrix[r, c])

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
    Progress(top, progress, times)
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


def CreateEquation():
    return "".join(map(str, Parts))


def UpdateText(window: tk.Misc, label: tk.Label, text: str):
    if window.winfo_exists() and label.winfo_exists():
        label.config(text=text)
        window.update_idletasks()
        window.geometry(f"{window.winfo_width()}x{window.winfo_reqheight()}")


def clearWindow(window: tk.Misc):
    for widget in window.winfo_children():
        widget.destroy()

def AddValue(value):
    Parts.append(value)
    UpdateText(Menu, new_input_label, str(value))
    UpdateText(Menu, equation_label, CreateEquation())

def DeleteValue():
    if (Parts):
        Parts.pop(-1)
        UpdateText(Menu, equation_label, CreateEquation())

def Calculate(window: tk.Tk, label: tk.Label):
    if (calculator.EquationIntegrity(Parts)):
        UpdateText(window, label, ("= " + calculator.Equal(Parts)))

def StartApp(window: tk.Tk):
    global new_input_label, equation_label
    window.title("Calculator")
    window.geometry("500x300")

    texts = CreateEquation()

    equation_label = tk.Label(window, text=texts, font=Font, justify="center")
    equation_label.grid(row=0, column=1, padx=5, pady=5)
    
    answer_label = tk.Label(window, text="=", font=Font, justify="right")
    answer_label.grid(row=0, column=2, padx=5, pady=5)

    new_input_label = tk.Label(window, text="", font=tkFont(weight="bold", size=14))
    new_input_label.grid(row=0, column=0, padx=20, pady=20)

    calculate_button = tk.Button(
        window,
        text="Calculate",
        bg="grey",
        width=24,
        height=2,
        command=lambda: Calculate(window, answer_label)
    )
    calculate_button.grid(row=2, column=0, padx=5, pady=5)
    
    # Should be removed later
    
    test_button = tk.Button(
        window,
        text="+",
        bg="grey",
        width=24,
        height=2,
        command=lambda: AddValue(" + ")
    )
    test_button.grid(row=2, column=1, padx=5, pady=5)
    
    test2_button = tk.Button(
        window,
        text="-",
        bg="grey",
        width=24,
        height=2,
        command=lambda: AddValue(" - ")
    )
    test2_button.grid(row=2, column=2, padx=5, pady=5)

def Progress(window: tk.Toplevel, progress: ttk.Progressbar, value: int):
    progress["value"] = value
    if (value == baselineReadingsNum):
        clearWindow(Menu)
        StartApp(Menu)
        window.destroy()

def StartCreatingBaseline():
    global top, progress
    top = tk.Toplevel(Menu)
    top.grab_set()
    top.focus_set()
    top.title("Calibration")
    top.resizable(False, False)

    text = "Calibrating in progress"

    note_label = tk.Label(top, text=text, font=Font, justify="center")
    note_label.grid(row=0, column=0, padx=5, pady=20)

    progress = ttk.Progressbar(top, orient="horizontal", length=300, mode="determinate")
    progress.grid(row=1, column=0, pady=30, padx=10)
    progress["maximum"] = baselineReadingsNum


async def DeviceFound():
    UpdateText(DeviceConnectionTop, DeviceConnectionTopLabel, "Device Found")
    await asyncio.sleep(2)

    if DeviceConnectionTop.winfo_exists():
        DeviceConnectionTop.destroy()

    StartCreatingBaseline()


def Connecting():
    global DeviceConnectionTop, DeviceConnectionTopLabel

    DeviceConnectionTop = tk.Toplevel(Menu)
    DeviceConnectionTop.grab_set()
    DeviceConnectionTop.focus_set()
    DeviceConnectionTop.title("Connecting...")
    DeviceConnectionTop.resizable(False, False)

    text = "Connecting to a device"

    DeviceConnectionTopLabel = tk.Label(DeviceConnectionTop, text=text, font=Font, justify="center")
    DeviceConnectionTopLabel.grid(row=0, column=0, padx=5, pady=20)

    asyncio.create_task(main())


def MainMenuWindow():
    global Menu
    Menu = tk.Tk()
    Menu.resizable(False, False)
    Menu.grid_rowconfigure(0, weight=1)
    Menu.grid_columnconfigure(0, weight=1)
    Menu.title("Smart Wearables App")

    text = "Only press the button,\nwhen the device sits comfortably on your wrist"

    note_label = tk.Label(Menu, text=text, font=Font, justify="center")
    note_label.grid(row=0, column=0, padx=10, pady=20)

    start_button = tk.Button(Menu, text="Connect", bg="grey", width=24, height=2, command=Connecting)
    start_button.grid(row=1, column=0, padx=5, pady=5)


def handle_notification(sender, data):
    global times, retained
    if len(data) != PACKET_SIZE:
        print(f"Wrong packet size: got {len(data)}, expected {PACKET_SIZE}")
        return

    values = struct.unpack(PACKET_FORMAT, data)

    backspace = values[0]
    matrix = values[1:]
    
    if IsBaseline:
        CreateBaselineData(backspace, matrix)
        return
    
    if backspace > Threshold(BaselineBackspace):
        print("Pressed")

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

        predicted_digit = int(np.where(confidences >= nullThreshold, y_pred, -1)[0])
        print(f"Predicted Digit: {predicted_digit}, confidence: {confidences[0]}")
        
        if (predicted_digit != -1):
            AddValue(predicted_digit)

        retained = np.zeros((1, N, N), dtype=int)
        times = 0

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
        UpdateText(DeviceConnectionTop, DeviceConnectionTopLabel, "Device not found")
        await asyncio.sleep(2)
        if DeviceConnectionTop.winfo_exists():
            DeviceConnectionTop.destroy()
        return

    await DeviceFound()

    async with BleakClient(target.address) as client:
        print("Connected to", target.name)
        await client.start_notify(CHAR_UUID, handle_notification)

        try:
            while True:
                await asyncio.sleep(1)
        finally:
            await client.stop_notify(CHAR_UUID)


async def tk_loop(root: tk.Tk):
    try:
        while True:
            root.update()
            await asyncio.sleep(0.01)
    except tk.TclError:
        pass

async def app():
    MainMenuWindow()
    await tk_loop(Menu)

asyncio.run(app())