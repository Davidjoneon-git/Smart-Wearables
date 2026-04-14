import tkinter as tk
from tkinter import ttk
import asyncio
import struct
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


def StartApp(window: tk.Tk):
    window.title("Calculator")
    window.geometry("400x200")

    texts = CreateEquation()

    equation_label = tk.Label(window, text=texts, font=Font, justify="center", wraplength=300)
    equation_label.grid(row=0, column=0, padx=5, pady=5)

    new_input_label = tk.Label(window, text="Nothing")
    new_input_label.grid(row=1, column=0, padx=20, pady=20)

    test_button = tk.Button(
        window,
        text="Test",
        bg="grey",
        width=24,
        height=2,
        command=lambda: UpdateText(window, equation_label, "Test")
    )
    test_button.grid(row=2, column=0, padx=5, pady=5)


def StartProgress(window: tk.Toplevel, progress: ttk.Progressbar, value: int):
    progress["value"] = value

    if value < 100:
        window.after(50, lambda: StartProgress(window, progress, value + 1))
    else:
        clearWindow(Menu)
        StartApp(Menu)
        window.destroy()


def StartCreateBaseline():
    global top
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

    StartProgress(top, progress, 0)


async def DeviceFound():
    UpdateText(DeviceConnectionTop, DeviceConnectionTopLabel, "Device Found")
    await asyncio.sleep(2)

    if DeviceConnectionTop.winfo_exists():
        DeviceConnectionTop.destroy()

    StartCreateBaseline()


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
    if len(data) != PACKET_SIZE:
        print(f"Wrong packet size: got {len(data)}, expected {PACKET_SIZE}")
        return

    values = struct.unpack(PACKET_FORMAT, data)

    backspace = values[0]
    matrix = values[1:]

    print("Backspace:", backspace)

    grid = [matrix[i * 8:(i + 1) * 8] for i in range(8)]
    for row in grid:
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


if __name__ == "__main__":
    asyncio.run(app())