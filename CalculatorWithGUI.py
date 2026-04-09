import tkinter as tk
from tkinter import ttk
import threading
import asyncio
import queue
import struct

from bleak import BleakScanner, BleakClient
import numpy as np
import tensorflow as tf


# =========================
# CONFIG
# =========================
FONT = ("Arial", 12)

DEVICE_NAME = "XIAO-ESP32S3"
CHAR_UUID = "abcdefab-1234-1234-1234-abcdefabcdef"

N = 8
NUM_VALUES = 65
PACKET_FORMAT = "<65H"
PACKET_SIZE = struct.calcsize(PACKET_FORMAT)

THRESHOLD_ADC = 0
PLUS_ADC = 500

MAX_TIMES = 60
BASELINE_READINGS_NUM = 500

MODEL_PATH = "ml_model.keras"


# =========================
# GLOBAL APP STATE
# =========================
data_queue = queue.Queue()

Menu = None
EquationLabel = None
NewInputLabel = None

ble_thread = None
ble_stop_event = None

model = None

Parts = [1, 2, 3, " + ", 3, 4, " - ", 4, 3, " - ", 3, 3, " + ", 3, 3, 3, 3]

retained = np.zeros((1, N, N), dtype=int)
times = 0

is_baseline = True
baseline_matrix_frames = []
baseline_backspace_frames = []

BaselineMatrix = np.zeros((N, N), dtype=float)
BaselineBackspace = 0.0


# =========================
# MODEL / DATA LOGIC
# =========================
def load_model_once():
    global model
    if model is None:
        model = tf.keras.models.load_model(MODEL_PATH)


def create_equation():
    return "".join(map(str, Parts))


def matrix_to_boolean(readings):
    output = np.zeros((1, N, N), dtype=bool)
    for r in range(N):
        for c in range(N):
            output[:, r, c] = readings[:, r, c] > (BaselineMatrix[r, c] + PLUS_ADC)
    return output


def update_matrix(readings):
    global retained
    for r in range(N):
        for c in range(N):
            retained[:, r, c] = max(readings[r][c], retained[:, r, c])


def create_baseline_data(backspace, matrix):
    global is_baseline, times, BaselineMatrix, BaselineBackspace

    baseline_matrix_frames.append(np.array(matrix).reshape(N, N))
    baseline_backspace_frames.append(backspace)

    times += 1
    progress_percent = int((times / BASELINE_READINGS_NUM) * 100)
    data_queue.put(("baseline_progress", min(progress_percent, 100)))

    if times >= BASELINE_READINGS_NUM:
        is_baseline = False
        times = 0

        mbuffer = np.array(baseline_matrix_frames)
        bbuffer = np.array(baseline_backspace_frames)

        BaselineMatrix = np.median(mbuffer, axis=0)
        BaselineBackspace = float(np.median(bbuffer))

        baseline_matrix_frames.clear()
        baseline_backspace_frames.clear()

        data_queue.put(("baseline_done", "Calibration complete"))


def handle_notification(sender, data):
    global times, retained

    if len(data) != PACKET_SIZE:
        data_queue.put(("status", f"Wrong packet size: got {len(data)}, expected {PACKET_SIZE}"))
        return

    values = struct.unpack(PACKET_FORMAT, data)

    backspace = values[0]
    matrix = values[1:]

    if is_baseline:
        create_baseline_data(backspace, matrix)
        return

    if backspace > THRESHOLD_ADC:
        data_queue.put(("status", "Backspace pressed"))

    grid = [matrix[i * 8:(i + 1) * 8] for i in range(8)]
    update_matrix(grid)
    times += 1

    if times == MAX_TIMES:
        sample_bool = matrix_to_boolean(retained)
        sample_feat = sample_bool.reshape(-1, N * N).astype(np.float32)

        prediction = model.predict(sample_feat, verbose=0)
        predicted_digit = int(np.argmax(prediction, axis=1)[0])

        data_queue.put(("digit", predicted_digit))

        retained = np.zeros((1, N, N), dtype=int)
        times = 0


# =========================
# BLE LOGIC
# =========================
async def ble_main(stop_event):
    global is_baseline, times, retained

    data_queue.put(("status", "Scanning for device..."))
    devices = await BleakScanner.discover()

    target = None
    for d in devices:
        if d.name == DEVICE_NAME:
            target = d
            break

    if target is None:
        data_queue.put(("status", "Device not found"))
        return

    data_queue.put(("device_found", f"Found {target.name}"))

    async with BleakClient(target.address) as client:
        data_queue.put(("status", f"Connected to {target.name}"))
        await client.start_notify(CHAR_UUID, handle_notification)

        while not stop_event.is_set():
            await asyncio.sleep(0.1)

        await client.stop_notify(CHAR_UUID)
        data_queue.put(("status", "BLE stopped"))


def start_ble_thread():
    global ble_thread, ble_stop_event

    if ble_thread and ble_thread.is_alive():
        return

    ble_stop_event = threading.Event()

    def runner():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(ble_main(ble_stop_event))
        except Exception as e:
            data_queue.put(("status", f"BLE error: {e}"))
        finally:
            loop.close()

    ble_thread = threading.Thread(target=runner, daemon=True)
    ble_thread.start()


def stop_ble():
    global ble_stop_event
    if ble_stop_event:
        ble_stop_event.set()


# =========================
# TKINTER HELPERS
# =========================
def clear_window(window):
    for widget in window.winfo_children():
        widget.destroy()


def fit_height_to_content(window, fixed_width=None):
    window.update_idletasks()
    if fixed_width is None:
        window.geometry(f"{window.winfo_reqwidth()}x{window.winfo_reqheight()}")
    else:
        window.geometry(f"{fixed_width}x{window.winfo_reqheight()}")


def update_text(window, label, text, fixed_width=None):
    label.config(text=text)
    fit_height_to_content(window, fixed_width)


def center_toplevel(top, parent):
    top.update_idletasks()

    parent_x = parent.winfo_rootx()
    parent_y = parent.winfo_rooty()
    parent_w = parent.winfo_width()
    parent_h = parent.winfo_height()

    top_w = top.winfo_reqwidth()
    top_h = top.winfo_reqheight()

    x = parent_x + (parent_w // 2) - (top_w // 2)
    y = parent_y + (parent_h // 2) - (top_h // 2)

    top.geometry(f"+{x}+{y}")


# =========================
# GUI SCREENS
# =========================
def start_app(window):
    global EquationLabel, NewInputLabel

    clear_window(window)

    window.title("Calculator")
    window.resizable(False, False)

    frame = tk.Frame(window)
    frame.pack(expand=True, fill="both", padx=10, pady=10)

    texts = create_equation()

    EquationLabel = tk.Label(
        frame,
        text=texts,
        font=FONT,
        justify="center",
        wraplength=300
    )
    EquationLabel.grid(row=0, column=0, padx=5, pady=5)

    NewInputLabel = tk.Label(
        frame,
        text="Nothing",
        font=FONT,
        justify="center",
        wraplength=300
    )
    NewInputLabel.grid(row=1, column=0, padx=20, pady=20)

    fit_height_to_content(window, 400)


def show_calibration_popup(parent):
    top = tk.Toplevel(parent)
    top.title("Calibration")
    top.transient(parent)
    top.grab_set()
    top.focus_set()
    top.resizable(False, False)

    label = tk.Label(top, text="Calibrating in progress", font=FONT, justify="center")
    label.grid(row=0, column=0, padx=10, pady=20)

    progress = ttk.Progressbar(top, orient="horizontal", length=300, mode="determinate", maximum=100)
    progress.grid(row=1, column=0, padx=10, pady=20)

    fit_height_to_content(top, 340)
    center_toplevel(top, parent)

    return top, label, progress


def show_connecting_popup(parent):
    top = tk.Toplevel(parent)
    top.title("Connecting...")
    top.transient(parent)
    top.grab_set()
    top.focus_set()
    top.resizable(False, False)

    label = tk.Label(top, text="Connecting to a device", font=FONT, justify="center")
    label.grid(row=0, column=0, padx=10, pady=20)

    fit_height_to_content(top, 320)
    center_toplevel(top, parent)

    return top, label


# =========================
# APP CONTROLLER
# =========================
connecting_top = None
connecting_label = None

calibration_top = None
calibration_label = None
calibration_progress = None


def connecting():
    global connecting_top, connecting_label

    connecting_top, connecting_label = show_connecting_popup(Menu)
    start_ble_thread()


def process_ble_data():
    global connecting_top, calibration_top, calibration_progress, calibration_label

    try:
        while True:
            msg_type, payload = data_queue.get_nowait()

            if msg_type == "status":
                if connecting_top is not None and connecting_top.winfo_exists():
                    update_text(connecting_top, connecting_label, payload, 320)

            elif msg_type == "device_found":
                if connecting_top is not None and connecting_top.winfo_exists():
                    update_text(connecting_top, connecting_label, "Device Found", 320)

                    def close_connecting_and_open_calibration():
                        global calibration_top, calibration_label, calibration_progress

                        if connecting_top is not None and connecting_top.winfo_exists():
                            connecting_top.destroy()

                        calibration_top, calibration_label, calibration_progress = show_calibration_popup(Menu)

                    Menu.after(800, close_connecting_and_open_calibration)

            elif msg_type == "baseline_progress":
                if calibration_top is not None and calibration_top.winfo_exists():
                    calibration_progress["value"] = payload

            elif msg_type == "baseline_done":
                if calibration_top is not None and calibration_top.winfo_exists():
                    update_text(calibration_top, calibration_label, "Calibration complete", 340)
                    calibration_progress["value"] = 100

                    def finish_calibration():
                        if calibration_top is not None and calibration_top.winfo_exists():
                            calibration_top.destroy()
                        start_app(Menu)

                    Menu.after(800, finish_calibration)

            elif msg_type == "digit":
                if EquationLabel is not None:
                    update_text(Menu, NewInputLabel, f"Predicted digit: {payload}", 400)

            else:
                pass

    except queue.Empty:
        pass

    Menu.after(50, process_ble_data)


def on_close():
    stop_ble()
    Menu.destroy()


def main_menu_window():
    global Menu

    load_model_once()

    Menu = tk.Tk()
    Menu.title("Smart Wearables App")
    Menu.resizable(False, False)
    Menu.protocol("WM_DELETE_WINDOW", on_close)

    frame = tk.Frame(Menu)
    frame.pack(expand=True, fill="both", padx=10, pady=10)

    text = "Only press the button,\nwhen the device sits comfortably on your wrist"

    note_label = tk.Label(frame, text=text, font=FONT, justify="center")
    note_label.grid(row=0, column=0, padx=10, pady=20)

    start_button = tk.Button(
        frame,
        text="Connect",
        bg="grey",
        width=24,
        height=2,
        command=connecting
    )
    start_button.grid(row=1, column=0, padx=5, pady=5)

    fit_height_to_content(Menu, 400)

    process_ble_data()
    Menu.mainloop()


if __name__ == "__main__":
    main_menu_window()